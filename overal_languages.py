import pandas as pd
import pymysql
from sqlalchemy import create_engine
from bokeh.io import output_file, show, save
from bokeh.plotting import figure
from bokeh.resources import Resources

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")

df_tweets = pd.read_sql_query("SELECT * FROM Tweets", engine)
tweets_language = df_tweets["lang"]
tweets_lang_freq = tweets_language.value_counts()

lang_set = []
for lang in tweets_lang_freq.index:
    lang_set.append(lang)

preqs = []
for preq in tweets_lang_freq:
    preqs.append(preq)

x = lang_set[0:10]
y = preqs[0:10]

p = figure(x_range=x, plot_height=250, title="Tweets by langugages",
           toolbar_location=None, tools="")
p.vbar(x=x, top=y, width=0.9)

p.xgrid.grid_line_color = None
p.y_range.start = 0

# save the result as html file, you will change to your path
save(p, filename="my_graphs/language_count.html", resources=Resources(mode="inline"), title="Tweets by langugages")