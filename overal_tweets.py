# This file is the overal statistic for the tweets collected

import pandas as pd
import pymysql
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")

tweet_df = pd.read_sql_query("SELECT * FROM Tweets", engine)

# Total tweets
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
