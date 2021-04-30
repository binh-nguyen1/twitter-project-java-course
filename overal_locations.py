import pandas as pd
import pymysql
from sqlalchemy import create_engine
from bokeh.io import output_file, show, save
from bokeh.plotting import figure
from bokeh.resources import Resources

# Make sure the password and name of database are correct
engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")

df_users = pd.read_sql_query("SELECT * FROM Users", engine)
locations = df_users["location"]
locations_freq = locations.value_counts()

locations_set = []
for location in locations_freq.index:
    locations_set.append(location)

preqs = []
for preq in locations_freq:
    preqs.append(preq)

x = locations_set[0:10]
y = preqs[0:10]

p = figure(x_range=x, plot_height=400, plot_width=1000, title="Location_count",
           toolbar_location=None, tools="")
p.vbar(x=x, top=y, width=0.5, color = "crimson")

p.xgrid.grid_line_color = None
p.y_range.start = 0

# save the result as html file, you will change to your path
save(p, filename="my_graphs/location_count.html", resources=Resources(mode="inline"), title="Location_count")