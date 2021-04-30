import pandas as pd
import pymysql
from sqlalchemy import create_engine
from bokeh.io import output_file, show, save
from bokeh.plotting import figure
from bokeh.resources import Resources

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/Twitter")

df_hashtags = pd.read_sql_query("SELECT * FROM Hashtags", engine)
hashtags_freq = df_hashtags["_text"].value_counts()

hashtag_set = []
for hashtag in hashtags_freq.index:
    hashtag_set.append(hashtag)

preqs = []
for preq in hashtags_freq:
    preqs.append(preq)

x = hashtag_set[0:10]
y = preqs[0:10]

p = figure(x_range=x, plot_height=400, plot_width=1000, title="Hashtags Trending",
           toolbar_location=None, tools="")
p.vbar(x=x, top=y, width=0.5, color = "lightskyblue")
p.line(x, y, line_width=2, color = "tomato")

p.xgrid.grid_line_color = None
p.y_range.start = 0

# save the result as html file, you will change to your path
save(p, filename="my_graphs/hashtag_count.html", resources=Resources(mode="inline"), title="Hashtags Trending")