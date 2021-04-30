# python file_name [user_id_str]
import os
import sys
import pymysql
from sqlalchemy import create_engine
import pandas as pd


if (len(sys.argv) == 2):
    user_id_arg = sys.argv[1]
else:
    raise RuntimeError("Invalid argument amount")

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")


sql_statement = "SELECT * FROM Tweets WHERE id_str IN (SELECT tweet_id_str FROM Said_by WHERE user_id_str = '%s')" % user_id_arg
tweet_df = pd.read_sql_query(sql_statement, engine)

sql_statement2 = "SELECT * FROM Users WHERE id_str = '%s'" % user_id_arg
user_df = pd.read_sql_query(sql_statement2, engine)

# User infomation
print("User information")
print("Name: %s" % user_df['_name'][0])
print("Screen Name: %s" % user_df['screen_name'][0])
print("Location: %s" % user_df['location'][0])
print("Number of Followers: %s" % user_df['followers_count'][0])
print("Number of Friends: %s" % user_df['friends_count'][0])
print("\n")
# Total tweets
print("Tweets Statistics")
print('Total tweets this period:', len(tweet_df.index), '\n')
# Retweets
tweet_df = tweet_df.sort_values(by='retweet_count', ascending=False)
tweet_df = tweet_df.reset_index(drop=True)
print ('Mean retweet_count:', round(tweet_df['retweet_count'].mean(),2), '\n')
print ('Top 5 RTed tweets:')
print ('------------------')
for i in range(5):
    print(tweet_df['id_str'][i], '-', tweet_df['retweet_count'][i])
print ('\n')
    
# Likes
tweet_df = tweet_df.sort_values(by='favorite_count', ascending=False)
tweet_df = tweet_df.reset_index(drop=True)
print ('Mean favorite_count:', round(tweet_df['favorite_count'].mean(),2), '\n')
print ('Top 5 liked tweets:')
print ('-------------------')
for i in range(5):
    print (tweet_df['id_str'][i], '-', tweet_df['favorite_count'][i])
print ('\n')

import matplotlib.pyplot as plt
# convert string of time into date time object
tweet_df['created_at'] = pd.to_datetime(tweet_df.created_at)
tweet_df_60min = tweet_df.groupby(pd.Grouper(key='created_at', freq='60Min', convention='start')).size()
tweet_df_60min.plot(figsize=(18,6), color = 'blue', linestyle = 'solid')

plt.ylabel('60 Minute Tweet Count')
plt.title('Tweet Freq. Count')
plt.grid(False)
plt.savefig('my_graphs/60min-timeline.png')

print("The timeline of activity is created!\n")