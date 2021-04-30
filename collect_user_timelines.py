# python file_name [user_id_str] [number_of_tweets]
import os
import signal
import sys
import redis
import tweepy
import toml
import pymysql
import json
import traceback
import time


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


TWITTER_CONSUMER_KEY = config["credentials"]["consumer_key"]
TWITTER_CONSUMER_SECRET = config["credentials"]["consumer_secret"]
TWITTER_ACCESS_TOKEN_KEY = config["credentials"]["access_token_key"]
TWITTER_ACCESS_TOKEN_SECRET = config["credentials"]["access_token_secret"]

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)


if (len(sys.argv) == 3):
    user_id_arg = sys.argv[1]
    number_tweets = float(sys.argv[2])
else:
    raise RuntimeError("Invalid argument amount")

db = pymysql.connect(user=USERNAME, passwd=PASSWORD, host=HOSTADDR, 
                    database=DATABASE_NAME)

# getting a tuple of all the user id's
cursor = db.cursor()
get_user_ids = ("SELECT id_str FROM Users where id_str = '%s'" % user_id_arg)
cursor.execute(get_user_ids)
user_ids = cursor.fetchall()


# functions for inserting into the db
# %s is just a placeholder for the data
add_tweet =         ("INSERT INTO Tweets VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
add_user =          ("INSERT INTO Users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
add_said_by =       ("INSERT INTO Said_by VALUES (%s, %s)")
add_hashtags =      ("INSERT INTO Hashtags VALUES (%s, %s)")
add_url =           ("INSERT INTO Urls VALUES (%s, %s)")
add_user_mentions = ("INSERT INTO User_mentions VALUES (%s, %s, %s, %s)")
add_media =         ("INSERT INTO Media VALUES (%s, %s, %s, %s, %s)")

users = set()
tweets = set()

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

# Fill the bucket with data and dump it into the database
bucket = []

def send(add, bucket):
    try:
        cursor.execute(add, tuple(bucket))
        # print("Try executed")
        bucket.clear()
    except pymysql.IntegrityError:      # duplicate data so move on
        # print("except executed")
        bucket.clear()
        # traceback.print_exc()


def id_checked(user_id):
    return red.sismember("retrieved_200", user_id) or red.sismember("deleted_user", user_id)


def SIGINT_handler(signum, frame):
    cursor.close()
    db.close()
    sys.exit(0)

# add more tweets function here
def add_more_tweet(status):
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

    if tweet_id and (tweet_id not in tweets):
        print ("Adding tweets", tweet_id)
        tweets.add(tweet_id)
        for field in tweet_fields:
            if field.startswith("last"):
                bucket.append(time_string)
                continue
            bucket.append(tweet_obj.get(field))

        if coords:
            bucket[9] = coords['coordinates'][0]
            bucket[10] = coords['coordinates'][1]

        # print(bucket)
        send(add_tweet, bucket)
        
        if user_id and (user_id not in users):     # if duplicate user then skip them
            users.add(user_id)                  # otherwise add it to the set
            for field in user_fields:
                if field == "location" and len(str(user_obj.get(field))) > 30:
                    bucket.append(None)   # filtering out some garbage i came across
                    continue
                if field.startswith("last"):
                    bucket.append(time_string)
                    continue
                bucket.append(user_obj.get(field))
            # print(bucket)
            # print("[add]", bucket[1], "with _name is ", bucket[2])
            send(add_user, bucket)
            # print("[finished]")
            # send(add_user, bucket)


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
    # total_insert += 1
    # print(f"{total_insert} inserted into db\n")

# quitin_time = False
signal.signal(signal.SIGINT, SIGINT_handler)

timelines_already_collected = True


auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)

api = tweepy.API(
    auth_handler=auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True
)

red = redis.Redis(host="127.0.0.1")


i = 0

for user_id in user_ids:
    user_id = user_id[0]
    print ("Collecting... user_id = ", user_id)
    if id_checked(user_id):
        continue
    timelines_already_collected = False
    try:
        statuses = api.user_timeline(user_id, count=number_tweets)
        for status in statuses:
            # print("Status info:")
            # print(status)
            add_more_tweet(status) # come from tweet collector --> suspect
        red.sadd("retrieved_200", user_id)
    except:
        red.sadd("deleted_user", user_id)
        traceback.print_exc()
    i += 1
    # if quitin_time:
    #     break
    if i % 100 == 0:
        print(f"{i} users retrieved")

# if timelines_already_collected:
#     os.remove(timelines_file)


# os.kill(os.getpid(), signal.SIGINT)

print("complete")
