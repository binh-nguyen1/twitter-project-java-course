# ./tweet_collector.py [keyword] [hashtag] minutes_to_run

import signal
import sys
import tweepy
import json
import time
import toml
import pymysql
import os

# toml must be named 'config.toml' and have a table named 'database' and 'credentials'
if not os.path.isfile("config.toml"):
    sys.exit("Must have config.toml file with Twitter credentials and database connection info.")

config = toml.load("config.toml")

if ("database" not in config):
    sys.exit("Missing 'database' table in config.toml")

if ("credentials" not in config):
    sys.exit("Missing 'credentials' table in config.toml")

USERNAME = config["database"]["username"]
PASSWORD = config["database"]["password"]
HOSTADDR = config["database"]["hostaddr"]
DATABASE_NAME = config["database"]["database_name"]

# Fall back time for the rate limit
TIMEOUT_BACKOFF = 60

TWITTER_CONSUMER_KEY = config["credentials"]["consumer_key"]
TWITTER_CONSUMER_SECRET = config["credentials"]["consumer_secret"]
TWITTER_ACCESS_TOKEN_KEY = config["credentials"]["access_token_key"]
TWITTER_ACCESS_TOKEN_SECRET = config["credentials"]["access_token_secret"]

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)

if (len(sys.argv) == 4):
    keyword = sys.argv[1]
    hashtag = sys.argv[2]
    minutes_to_run = float(sys.argv[3])
elif (len(sys.argv) == 3):
    keyword = sys.argv[1]
    minutes_to_run = float(sys.argv[2])
    hashtag = ""
else:
    raise RuntimeError("Invalid argument amount")

db = pymysql.connect(user=USERNAME, passwd=PASSWORD, host=HOSTADDR, 
                    database=DATABASE_NAME)

cursor = db.cursor()    # used to insert and update

# used to skip duplicate users and tweets
users = set()
tweets = set()
# Fill the bucket with data and dump it into the database
bucket = []
total_insert = 0
# Used to compare to the current time
start_time = time.time()
time_string = ""
seconds = minutes_to_run * 60

tweet_fields = [
    "id_str",
    "text",
    "created_at",
    "source",
    "quote_count",
    "reply_count",
    "retweet_count",
    "favorite_count",
    "lang",
    "x_coor",
    "y_coor",
    "last_updated",
    "last_accessed",
    "in_reply_to_user_id",      #v2 addition
    "conversation_id"          #v2 addition

]

user_fields = [
    "id_str",
    "screen_name",
    "name",
    "created_at",
    "location",
    "followers_count",
    "friends_count",
    "listed_count",
    "statuses_count",
    "default_profile",
    "default_profile_image",
    "last_updated",
    "last_accessed",
    "protected",           #v2 addition
    "verified"             #v2 addition
]

# functions for inserting into the db
# %s is just a placeholder for the data
add_tweet =         ("INSERT INTO Tweets VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
add_user =          ("INSERT INTO Users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
add_said_by =       ("INSERT INTO Said_by VALUES (%s, %s)")
add_hashtags =      ("INSERT INTO Hashtags VALUES (%s, %s)")
add_url =           ("INSERT INTO Urls VALUES (%s, %s)")
add_user_mentions = ("INSERT INTO User_mentions VALUES (%s, %s, %s, %s)")
add_media =         ("INSERT INTO Media VALUES (%s, %s, %s, %s, %s)")

def send(add, bucket):
    try:
        cursor.execute(add, tuple(bucket))
        bucket.clear()
    except pymysql.IntegrityError:      # duplicate data so move on
        bucket.clear()

def sort_tweet(status):
    global TIMEOUT_BACKOFF
    global total_insert
    # Used to initalize the updated and accessed times
    current = time.localtime()
    time_string = time.strftime("%a %b %d %H:%M:%S %Y", current)
    
    tweet = json.dumps(status._json)
    tweet_obj = json.loads(tweet)
    tweet_id = tweet_obj['id_str']
    user_obj = tweet_obj['user']
    user_id = user_obj['id_str']
    hashtag_obj = tweet_obj['entities']['hashtags']
    url_obj = tweet_obj['entities']['urls']
    user_mention_obj = tweet_obj['entities']['user_mentions']
    coords = tweet_obj['coordinates']

    if tweet_id or tweet_id not in tweets:
        tweets.add(tweet_id)
        for field in tweet_fields:
            if field.startswith("last"):
                bucket.append(time_string)
                continue
            if (field == 'conversation_id'):
                continue;
            bucket.append(tweet_obj.get(field))

        if coords:
            bucket[9] = coords['coordinates'][0]
            bucket[10] = coords['coordinates'][1]

        tbd = None
        bucket.append(tbd)
        # print(bucket)
        send(add_tweet, bucket)
        
        if user_id or user_id not in users:     # if duplicate user then skip them
            users.add(user_id)                  # otherwise add it to the set
            for field in user_fields:
                if field == "location" and len(str(user_obj.get(field))) > 30:
                    bucket.append(None)   # filtering out some garbage i came across
                    continue
                if field.startswith("last"):
                    bucket.append(time_string)
                    continue
                bucket.append(user_obj.get(field))
            send(add_user, bucket)

        # for the Said_by table
        bucket.append(tweet_id)
        bucket.append(user_id)
        send(add_said_by, bucket)
        
        if hashtag_obj:
            for dic in hashtag_obj:
                for key in dic.keys():
                    if key == 'text':
                        bucket.clear()
                        bucket.append(dic[key])
                        bucket.append(tweet_id)
                        send(add_hashtags, bucket)
            
        if url_obj:
            for dic in url_obj:
                for key in dic.keys():
                    if key == 'expanded_url':
                        bucket.append(dic[key])
                        bucket.append(tweet_id)
                        send(add_url, bucket)

        if user_mention_obj:
            for dic in user_mention_obj:
                for key in dic.keys():
                    if key in ['id_str', 'name', 'screen_name']:
                        bucket.append(dic[key])
                bucket.append(tweet_id)
                send(add_user_mentions, bucket)

        if 'media' in tweet_obj['entities']:
            media_obj = tweet_obj['entities']['media']
            for dic in media_obj:
                for key in dic.keys():
                    if key in ['display_url', 'id_str', 'source_status_id_str', 'type']:
                        bucket.append(dic[key])
                if len(bucket) != 4:
                    bucket.clear()
                    continue
                bucket.append(tweet_id)
                send(add_media, bucket)

    bucket.clear()
    db.commit()
    total_insert += 1
    # print(f"{total_insert} inserted into db\n")


class CustomStreamListener (tweepy.StreamListener):
    def __init__ (self, api=None):
        self.api = api
        # Formatted with 1 json tweet object per line
        # self.outfile = open(filepath, "w")
        
    def on_status(self, status): #this is where we do stuff with the data
        global TIMEOUT_BACKOFF
        global total_insert
        if (time.time() >= start_time + seconds):
            os.kill(os.getpid(), signal.SIGINT)

        TIMEOUT_BACKOFF = 60

        sort_tweet(status)

    
    def on_error(self, status_code):
        global TIMEOUT_BACKOFF
        global time_string
        # Exponential backoff if you get rate limited
        # Twitter purposely doesn't publish the number of requests for rate limiting
        if status_code == 420:
            print("Rate Limit: {time_string}\n\tsleeping for: {TIMEOUT_BACKOFF} seconds")
            time.sleep(TIMEOUT_BACKOFF)
            TIMEOUT_BACKOFF *= 2
            return True
            
    def close (self):
        print("\nCustomStreamListener closing...")
        cursor.close()
        db.close()

class StreamWrapper:
    def __init__ (self):
        self.streamListener = CustomStreamListener()
        self.stream = tweepy.Stream(auth = auth, listener=self.streamListener)

    def close (self):
        self.stream.disconnect()
        self.streamListener.close()

    def filter(self, follow=None, track=None, is_async=False, locations=None,
            stall_warnings=False, languages=None, encoding='utf8', filter_level=None):
        self.stream.filter(follow, track, is_async, locations,
                        stall_warnings, languages, encoding, filter_level)

# Just so we can disconnect and close the file
def signal_handler(sig, frame):
    stream.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

stream = StreamWrapper()

# Filters are case-insensitive
stream.filter(track=[
    keyword, # keyword
    hashtag, # hashtag
    # 'this matches a phrase', # must contain each word in phrase (irrespective of order)
    # 'phrase a matches this', # this will match the same tweets as the phrase above
])