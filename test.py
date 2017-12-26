#!/usr/bin/env python
import main
import json
import sys
import telepot
from telegram import TelegramBot
from twitter import Twitter
import time

def test_get_coins_bittrex():
	main.get_coins_bittrex()
	assert len(main.symbol_name) > 0
	assert len(main.name_symbol) > 0
	assert main.symbol_name["BTC"] == "bitcoin"
	assert main.name_symbol["bitcoin"] == "BTC"

def test_extract_symbols():
	main.get_coins_bittrex()
	texts = [
		'Coin of the day: Digibyte (DGB). Using a Blockchain which is 40 times faster than Bitcoin and having one of the most decentralized mining systems in the world - based on 5 different synergistic algorithms. DGB adherents call the coin "The Sleeping Giant".',
		'Yes, there are 1,500+ coins now. And yes, most  are jokes or outright scams. But among those coins are Ethereum, Monero, Litecoin and other proven winners. By implying Sether is a joke is a huge mistake. Go to sether.io and read it. You will see it is in the mold of a winner.',
		'Coin of the day: BURST -- First truly Green coin and most overlooked coin. Uses 400 times less power than Bitcoin. Super secure and private. Includes smart contracts, encrypted messaging, decentralized wallet, libertine blockchain. Most undervalued coin. https://www.burst-coin.org '
	]
	symbols = [
		set([('BTC', 'bitcoin'), ('DGB', 'digibyte')]),
		set([('XMR', 'monero'), ('LTC', 'litecoin'), ('ETH', 'ethereum')]),
		set([('BURST', 'burstcoin'), ('BTC', 'bitcoin')])
	]

	for i, text in enumerate(texts):
		extracted = main.extract_symbols(text)
		try:
			assert extracted == symbols[i]
		except AssertionError as e:
			print(extracted, symbols[i])
			raise e

def test_get_sentiment_analysis():
	coins = [
		("BTC", "bitcoin"),
		("BCH", "bitcoin cash")
	]
	text = "Bitcoin is good. BCH is bad."
	sentiment, overall = main.get_sentiment_analysis(text, coins)

	assert coins[0] in sentiment
	assert coins[1] in sentiment
	assert sentiment[coins[0]] > 0
	assert sentiment[coins[1]] < 0

	coins = [
		("DGB", "digibyte")
	]
	text = 'Coin of the day: Digibyte (DGB). Using a Blockchain which is 40 times faster than Bitcoin and having one of the most decentralized mining systems in the world - based on 5 different synergistic algorithms. DGB adherents call the coin "The Sleeping Giant".'
	sentiment, overall = main.get_sentiment_analysis(text, coins)

	assert overall > 0

def test_get_verdict():
	sentiment = {
		('DGB', 'digibyte'): 0.0,
		('BCH', 'bitcoin cash'): -0.6
	} 
	overall = 0.167
	to_buy = main.get_verdict(sentiment, overall)

	assert to_buy == [('DGB', 'digibyte')]

def test_analyze():
	main.get_coins_bittrex()
	
	# Negative sentiment
	text = "do not buy dogecoin, it is bad"
	to_buy = main.analyze(text)
	assert len(to_buy) == 0
	
	# Positive sentiment
	text = "please buy dogecoin"
	to_buy = main.analyze(text)
	assert len(to_buy) == 1

def test_twitter_tweet_callback(run_forever):
	main.get_coins_bittrex()
	main.bot = TelegramBot()
	text = "please buy doge"
	user = "mcafee2cash"
	link = "https://twitter.com/mcafee2cash/status/944746808466698240"
	
	try:
		main.twitter_tweet_callback(text, user, link)
	except Exception as e:
		raise AssertionError(e)
	
	if run_forever:
		while True:
			time.sleep(1)

def test_telegram_summary():
	main.get_coins_bittrex()
	main.bot = TelegramBot()
	query_data = "summary_doge"
	try:
		replies = main.bot.get_query_replies(query_data)
		assert len(replies) > 0
		assert len(replies[0]) == 2
		assert type(replies[0][0]) is str
		assert type(replies[0][1]) is telepot.namedtuple.InlineKeyboardMarkup
	except Exception as e:
		raise AssertionError(e)

def test_telegram_buy():
	main.get_coins_bittrex()
	main.bot = TelegramBot()
	query_data = "buy_doge"
	try:
		replies = main.bot.get_query_replies(query_data)
		assert len(replies) > 0
		assert len(replies[0]) == 2
		assert type(replies[0][0]) is str
	except Exception as e:
		raise AssertionError(e)

def test_tweet_handler():
	with open("test-data.json") as f:
		sample_tweets = json.load(f)
	
	Twitter.handle_tweet(None, tweet_json=sample_tweets["tweet_image"])

def test_main():
	with open("test-data.json") as f:
		sample_tweets = json.load(f)

	# Populate coins
	main.get_coins_bittrex()
	# Telegram bot
	bot = TelegramBot()
	# Twitter stream
	class MockTwitter:
		def tweet_callback(text, user, link):
			to_buy = main.analyze(text)
			assert len(to_buy) > 0
			bot.notify_tweet(text, user, link, to_buy)
	
	tweets = [
		sample_tweets["tweet_image"],
		sample_tweets["tweet_text"]
	]

	count = 0
	for tweet in tweets:
		Twitter.handle_tweet(MockTwitter, tweet_json=tweet)
		count += 1

	while count < len(tweets):
		time.sleep(1)

def test_twitter():
	twitter = Twitter()

if __name__ == "__main__":
	tests = {
		"get_coins_bittrex": test_get_coins_bittrex,
		"extract_symbols": test_extract_symbols,
		"get_sentiment_analysis": test_get_sentiment_analysis,
		"get_verdict": test_get_verdict,
		"analyze": test_analyze,
		"telegram_summary": test_telegram_summary,
		"telegram_buy": test_telegram_buy,
		"tweet_handler": test_tweet_handler
	}
	test_queue = {}
	try:
		if "(" in sys.argv[1]:
			eval(sys.argv[1])
			print("Test passed.")
			sys.exit()
		elif len(sys.argv[1:]) == 0:
			raise IndexError
		for test_name in sys.argv[1:]:
			test_queue[test_name] = tests[test_name]
	except KeyError as e:
		raise e
	except IndexError:
		test_queue = tests
	except Exception as e:
		raise e
	
	for test_name in test_queue.keys():
		try:
			test_queue[test_name]()
		except AssertionError as e:
			print(f'Test: {test_name} failed')
			raise e
		print(f'\tTest: {test_name} passed')
	print(f'{len(test_queue)} tests passed.')