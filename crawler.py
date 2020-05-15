import configparser
import couchdb
import time
import tweepy
from googletrans import Translator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Read configuration file
config = configparser.ConfigParser()
config.read('config.ini')

server_count = int(config.get('server', 'server_count'))
hostname = config.get('server', 'hostname')
address = config.get('server', 'address')
proxy = config.get('server', 'proxy')

max_id = config.get('twitter', 'max_id')
scale = int(config.get('twitter', 'scale'))

server_id = config.get('id', hostname)
task = 'task' + server_id
consumer_key = config.get(task, 'consumer_key')
consumer_secret = config.get(task, 'consumer_secret')
access_token_key = config.get(task, 'access_token_key')
access_token_secret = config.get(task, 'access_token_secret')

username = config.get('couchdb', 'username')
password = config.get('couchdb', 'password')
database = config.get('couchdb', 'database')
database_s = config.get('couchdb', 'database_s')

# Create tweepy API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)
# api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, proxy=proxy)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# Connect to CouchDB
couch = couchdb.Server('http://{}:5984'.format(address))
couch.resource.credentials = (username, password)

# Create database if not exist
try:
    couch.create(database)
except couchdb.http.PreconditionFailed:
    pass
db = couch[database]

try:
    couch.create(database_s)
except couchdb.http.PreconditionFailed:
    pass
db_s = couch[database_s]

# Sentiment analysis tool
translator = Translator()
analyser = SentimentIntensityAnalyzer()

twitter_count = 0
while True:
    # Set search range
    flag = int(max_id[:19-scale]) % server_count == int(server_id) - 1
    since_id = str(int(max_id[:19-scale]) - 1) + '0' * (scale - 1) + '1'
    temp = max_id

    # Check if the search range belongs to the application
    while flag:

        # Search tweets
        try:
            newTweets = api.search(geocode='-27,135,2000km', since_id=since_id, max_id=temp, count=100)
        except Exception as e:
            print(e)
            time.sleep(60)
            break

        # Finish searching the given range of tweets
        if not newTweets:
            print('Data from ' + since_id + ' to ' + max_id + ' crawled!')
            print('twitter count: ' + str(twitter_count))
            break

        # Write to database
        for tweet in newTweets:
            doc = tweet._json
            if doc['geo']:
                # Unique identifier
                doc['_id'] = doc['id_str']

                lang = doc['lang']
                text = doc['text']
                if lang == 'en':
                    en_text = text
                else:
                    try:
                        en_text = translator.translate(text).text
                    except Exception as e:
                        print(e)
                        continue

                sentiment = analyser.polarity_scores(en_text)
                sentiment['_id'] = doc['id_str']

                try:
                    db.save(doc)
                    db_s.save(sentiment)
                    twitter_count += 1
                except Exception as e:
                    print(e)
                    continue

        temp = str(newTweets[-1].id - 1)

    # Rewrite max id in configuration file
    max_id = str(int(since_id) - 1)
    config.set('twitter', 'max_id', max_id)
    config.write(open('config.ini', mode='w'))
