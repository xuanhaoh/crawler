import configparser
import couchdb
import os
import tweepy
from googletrans import Translator
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Read configuration file
config = configparser.ConfigParser()
config.read('config.ini')

hostname = os.getenv('HOST', None)
address = os.getenv('IP', None)
proxy = config.get('server', 'proxy')
nltk.set_proxy(proxy)
nltk.download('vader_lexicon')

server_id = config.get('id', hostname)
task = 'task' + server_id
consumer_key = config.get(task, 'consumer_key')
consumer_secret = config.get(task, 'consumer_secret')
access_token_key = config.get(task, 'access_token_key')
access_token_secret = config.get(task, 'access_token_secret')

username = config.get('couchdb', 'username')
password = config.get('couchdb', 'password')
database_raw = config.get('couchdb', 'database_raw')
database_processed = config.get('couchdb', 'database_processed')

# Connect to CouchDB
couch = couchdb.Server('http://{}:5984'.format(address))
couch.resource.credentials = (username, password)

# Create database if not exist
try:
    db_raw = couch[database_raw]
except couchdb.http.ResourceNotFound:
    db_raw = couch.create(database_raw)

try:
    db_processed = couch[database_processed]
except couchdb.http.ResourceNotFound:
    db_processed = couch.create(database_processed)

print('Connected to CouchDB!')

# Sentiment analysis tool
translator = Translator(proxies={'http': proxy, 'https': proxy})
sid = SentimentIntensityAnalyzer()

# Create tweepy API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, proxy=proxy)

print('Connected to Twitter API!')


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        doc = status._json
        if doc['place']:
            doc['_id'] = doc['id_str']
            text = doc['text']

            try:
                en_text = translator.translate(text).text
            except Exception as e:
                en_text = text
                print(e)

            sentiment = {key: value for key, value in doc.items() if key in ['_id', 'text', 'place', 'lang']}
            sentiment.update({'sentiment': sid.polarity_scores(en_text)})
            print(sentiment)

            try:
                db_raw.save(doc)
                db_processed.save(sentiment)
            except Exception as e:
                print(e)

    def on_error(self, status_code):
        print(status_code)


myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener, proxies={'http': proxy, 'https': proxy})
myStream.filter(locations=[113, -44, 154, -10])
