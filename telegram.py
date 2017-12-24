#!/usr/bin/env python
import bittrex_utils
from bittrex_utils import BittrexUtils
import json
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.loop import MessageLoop

with open("secrets.json") as f:
	keys = json.load(f)
	BOT_TOKEN = keys["TELEGRAM_BOT_TOKEN"]

class TelegramBot:
	def __init__(self, chat_id=176900492, order_callback=lambda x: x):
		self.chat_id = chat_id
		self.order_callback = order_callback
		self.bot = telepot.Bot(BOT_TOKEN)
		self.bittrex_utils = BittrexUtils()
		self.buying = None
		MessageLoop(self.bot, {
			"chat" : self.chat_handler,
			"callback_query": self.callback_query_handler
		}).run_as_thread()
		print("Running bot...")
	
	def get_chat_replies(self, msg):
		replies = []
		if msg["text"] == "/start":
			reply = ("I will notify you when crypto people tweet and give you buying options.", None)
			replies.append(reply)
		elif msg["text"] == "/cancel" and self.buying:
			self.buying = None
			reply = ("Cancelled buy.", None)
			replies.append(reply)
		elif self.buying:
			try:
				amount = float(msg["text"])
				# Buy
				pair, ask, quantity = self.bittrex_utils.buy_in_btc(self.buying, amount)
				reply = (f'Buying {quantity} {self.buying} @ {"{0:.8f}".format(ask)} BTC for {amount} BTC', None)
				replies.append(reply)
			except Exception as e:
				replies.append(("Please enter a valid number (up to 8 decimal places) e.g.", None))
				replies.append(("0.00000001", None))
		
		return replies

	def get_query_replies(self, query_data):
		query_type, coin = query_data.split("_")

		replies = []

		if query_type == "summary":
			summary = bittrex_utils.summary_bittrex(coin)
			message = f"""Market Summary for {coin}\n\nBid: {summary["bid"]}\nAsk: {summary["ask"]}\nLast: {summary["ask"]}\nYesterday: {summary["yesterday"]}\nChange: {summary["change"]}%\nVolume: {summary["volume"]} BTC\n\n(https://bittrex.com/Market/Index?MarketName=BTC-{coin})"""			
			button = [InlineKeyboardButton(text=f'Buy {coin} on Bittrex', callback_data=f'buy_{coin}')]
			keyboard = InlineKeyboardMarkup(inline_keyboard=[button])
			replies.append((message, keyboard))
		elif query_type == "buy":
			self.buying = coin
			replies.append((f"Send me an amount in BTC or /cancel ({self.bittrex_utils.get_available_balance()} BTC available)", None))

		return replies

	def chat_handler(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		if not chat_id == self.chat_id:
			return

		replies = self.get_chat_replies(msg)

		for reply in replies:
			messsage, keyboard = reply
			self.bot.sendMessage(self.chat_id, messsage, reply_markup=keyboard)

	def callback_query_handler(self, msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
		
		self.bot.answerCallbackQuery(query_id, text='Got it')

		replies = self.get_query_replies(query_data)

		for reply in replies:
			messsage, keyboard = reply
			self.bot.sendMessage(self.chat_id, messsage, reply_markup=keyboard)
	
	def notify_tweet(self, tweet_text, user, link, to_buy):
		buying_options = [InlineKeyboardButton(text=f'{x[1][0].upper()}{x[1][1:]} ({x[0]})', callback_data=f'summary_{x[0]}') for x in to_buy]
		keyboard = InlineKeyboardMarkup(inline_keyboard=[buying_options])
		message = f'{user}: "{tweet_text}"\n({link})'
		self.bot.sendMessage(self.chat_id, message, reply_markup=keyboard)
