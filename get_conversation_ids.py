import signal
import sys
import tweepy
import json
import time
import toml
import pymysql
import os
import base64
import requests
import socket
import errno


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
rateLimited = False
TIMEOUT_BACKOFF = 60

TWITTER_CONSUMER_KEY = config["credentials"]["consumer_key"]
TWITTER_CONSUMER_SECRET = config["credentials"]["consumer_secret"]
TWITTER_ACCESS_TOKEN_KEY = config["credentials"]["access_token_key"]
TWITTER_ACCESS_TOKEN_SECRET = config["credentials"]["access_token_secret"]

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)

db = pymysql.connect(user=USERNAME, passwd=PASSWORD, host=HOSTADDR, 
                    database=DATABASE_NAME)

cursor = db.cursor()    # used to insert and update

tweets_in_database = cursor.execute("SELECT id_str from Tweets;")
tweets = cursor.fetchall()

counter = 0

add_conversation_id = ("UPDATE twitterv2.Tweets SET conversation_id = %s WHERE id_str = %s;")


# Fill the bucket with data and dump it into the database
bucket = []

def send(add, bucket):
    cursor.execute(add_conversation_id, tuple(bucket))
    bucket.clear()
    db.commit()





def get_bearer_header():
   uri_token_endpoint = 'https://api.twitter.com/oauth2/token'
   key_secret = "{twitter_creds.consumer_key}:{twitter_creds.consumer_key_secret}".encode('ascii')
   b64_encoded_key = base64.b64encode(key_secret)
   b64_encoded_key = b64_encoded_key.decode('ascii')

   auth_headers = {
       'Authorization': 'Basic {}'.format(b64_encoded_key),
       'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
       }

   auth_data = {
       'grant_type': 'client_credentials'
       }

   bearer_token = config['bearer_token']['bearer_token']

   bearer_header = {
       'Accept-Encoding': 'gzip',
       'Authorization': 'Bearer {}'.format(bearer_token),
       'outh_consumer_key': TWITTER_CONSUMER_KEY
   }
   return bearer_header

def on_error(status_code):
    global TIMEOUT_BACKOFF
    global time_string
    global rateLimited
    time_string = "300 Per user Per 15 minute window for Tweet lookup"
    print(status_code)
    # Exponential backoff if you get rate limited
    # Twitter purposely doesn't publish the number of requests for rate limiting
    if status_code == "<Response [429]>":
        print("Rate Limit: " + str(time_string) + "\n\tsleeping for: " + str(TIMEOUT_BACKOFF) + " seconds")
        time.sleep(TIMEOUT_BACKOFF)
        TIMEOUT_BACKOFF *= 2
        if TIMEOUT_BACKOFF == 960:
           TIMEOUT_BACKOFF = 60
        return True


#code from stackoverflow to get conversation_id, with a few changes
uri = 'https://api.twitter.com/2/tweets?'

for tweet in tweets:
    
            
    params = {
        'ids':tweet,
        'tweet.fields':'conversation_id'
    }
    bearer_header = get_bearer_header()
    
    
    
    
    
    try:
        s = requests.session()
        resp = s.get(uri, headers = bearer_header, params = params)
        resp_json = resp.json()['data'][0]['conversation_id']
        counter += 1
        print(counter)
        bucket.append(resp_json)
        bucket.append(tweet)
        resp.close()

           
    except:
        #status code returned instead of data. NULL sent to database
        if str(resp) == '<Response [200]>':
           print('Something went wrong with this tweet')
           resp_json = None
           resp.close()
           counter += 1
           print(counter)
           bucket.append(resp_json)
           bucket.append(tweet)
               
               
            #rate limit has been reached, so program must wait
            #until conversation_ids can be pulled again
        if str(resp) == '<Response [429]>':
            rateLimited = True
            while rateLimited == True:
              resp.close()
              s.close()
              s = requests.session()
              on_error(str(resp))
                  #retry to get conversation_id from when rate limited
              try:
                     
                resp = s.get(uri, headers = bearer_header, params = params)
                resp_json = resp.json()['data'][0]['conversation_id']
                counter += 1
                print(counter)
                     
                rateLimited = False
                print("After waiting")
                bucket.append(resp_json)
                bucket.append(tweet)
                TIMEOUT_BACKOFF = 60
                resp.close()
                                    
              except:
                #status code returned instead of conversation_id. NULL sent to database
                if str(resp) == '<Response [200]>':
                    rateLimited = False
                    print('Something went wrong with this tweet')
                    resp_json = None
                    counter += 1
                    print(counter)
                    bucket.append(resp_json)
                    bucket.append(tweet)
                    resp.close()
                     
                #still rate limited so wait longer with exponential backoff   
                if str(resp) == '<Response [429]>':
                    rateLimited = True
               
    #add tweet object to database
    send(add_conversation_id, bucket)
cursor.close()    
