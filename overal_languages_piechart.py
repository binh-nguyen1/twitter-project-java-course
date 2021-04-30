from math import pi
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from bokeh.io import output_file, show, save
from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")

df_tweets = pd.read_sql_query("SELECT * FROM Tweets", engine)
tweets_language = df_tweets["lang"]
tweets_lang_freq = tweets_language.value_counts()

x = tweets_lang_freq

data = pd.Series(x).reset_index(name='value').rename(columns={'index':'language'})
data['angle'] = data['value']/data['value'].sum() * 2*pi
data['color'] = Category20c[len(x)]

p = figure(plot_height=350, title="Languges Pie Chart", toolbar_location=None,
           tools="hover", tooltips="@language: @value", x_range=(-0.5, 1.0))

p.wedge(x=0, y=1, radius=0.4,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field='language', source=data)

p.axis.axis_label=None
p.axis.visible=False
p.grid.grid_line_color = None

# save the result as html file, you will change to your path
save(p, filename="my_graphs/language_piechart.html", resources=Resources(mode="inline"), title="Tweets by langugages pie chart")