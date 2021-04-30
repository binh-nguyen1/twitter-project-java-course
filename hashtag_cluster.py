# Output is the number of graphs of hashtags clustering
# python clustering.py [number of cluster]

import sys
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from bokeh.io import output_file, show, save
from bokeh.plotting import figure
from bokeh.resources import Resources

import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

from wordcloud import WordCloud

# ---------------------------
# Clustering hagtags		-
# ---------------------------

if (len(sys.argv) == 2):
    true_k = sys.argv[1]
else:
    raise RuntimeError("Invalid argument amount")

true_k = int(true_k)

engine = create_engine("mysql+pymysql://root:Red060992@#@localhost/TwitterV2")

df_hashtags = pd.read_sql_query("SELECT * FROM Hashtags where tweet_id IN (SELECT id_str FROM Tweets WHERE lang = 'en')", engine)

hashtags = df_hashtags["_text"]
hashtags_freq = df_hashtags["_text"].value_counts() 

hashtag_set = []
for hashtag in hashtags_freq.index:
    hashtag_set.append(hashtag)

# print(hashtag_set)

from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(stop_words={'english'})
X = vectorizer.fit_transform(hashtags)

print(X.shape)
# print(vectorizer.get_feature_names())

# print(X[0,])

Sum_of_squared_distances = []
K = range(2,10)
for k in K:
    km = KMeans(n_clusters=k, max_iter=200, n_init=10)
    km = km.fit(X)
    Sum_of_squared_distances.append(km.inertia_)

# plt.plot(K, Sum_of_squared_distances, 'bx-')
# plt.xlabel('k')
# plt.ylabel('Sum_of_squared_distances')
# plt.title('Elbow Method For Optimal k')
# plt.show()

model = KMeans(n_clusters=true_k, init='k-means++', max_iter=200, n_init=10)
model.fit(X)
labels=model.labels_
title = hashtag_set
hashtag_cl=pd.DataFrame(list(zip(title,labels)),columns=['title','cluster'])
print(hashtag_cl.sort_values(by=['cluster']))

# visualization ML
# word cloud
result={'cluster':labels,'hagtags':hashtags}
result=pd.DataFrame(result)
for k in range(0,true_k):
    s=result[result.cluster==k]
    text=s['hagtags'].str.cat(sep=' ')
    text=text.lower()
    text=' '.join([word for word in text.split()])
    
    
    print('Cluster: {}'.format(k))
    print('Titles')
    titles=hashtag_cl[hashtag_cl.cluster==k]['title']
    words = titles.to_string(index=False)
    
    wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white").generate(words)
    print(titles.to_string(index=False))
    plt.figure()
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    # plt.show()
    plt.savefig('my_graphs/cluster%s.png'%k)