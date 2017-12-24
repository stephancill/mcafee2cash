from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json

with open("config.json") as f:
	config = json.load(f)
	FOLLOW_IDS = config["TWITTER_FOLLOW_IDS"]

with open("secrets.json") as f:
	keys = json.load(f) 
	CONSUMER_KEY = keys["TWITTER_CONSUMER_KEY"]
	CONSUMER_SECRET = keys["TWITTER_CONSUMER_SECRET"]
	ACCESS_KEY = keys["TWITTER_ACCESS_KEY"]
	ACCESS_SECRET = keys["TWITTER_ACCESS_SECRET"]

class TwitterListener(StreamListener):
	def __init__(self, callback):
		self.callback = callback

	def on_data(self, data):
		tweet_json = json.loads(data)
		self.callback(tweet_json)
		
class Twitter:
	def __init__(self, ids=FOLLOW_IDS, tweet_callback=lambda x: x):
		self.tweet_callback = tweet_callback
		
		self.listener = TwitterListener(self.handle_tweet)
		
		self.auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
		self.auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)

		self.stream = Stream(self.auth, self.listener)	
		self.stream.filter(follow=ids)
	
	def handle_tweet(self, tweet_json):
		screen_name = tweet_json["user"]["screen_name"]
		id = tweet_json["id_str"]
		text = tweet_json["text"]
		link = f'https://twitter.com/{screen_name}/status/{id}'
		self.tweet_callback(text, screen_name, link)

	