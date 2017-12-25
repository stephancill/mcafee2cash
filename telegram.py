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
		self.order_callback = order_callback
		self.bot = telepot.Bot(BOT_TOKEN)
		self.bittrex_utils = BittrexUtils()
		self.chat_id = None

		# Orders
		self.buying = None
		self.selling = None

		MessageLoop(self.bot, {
			"chat" : self.chat_handler,
			"callback_query": self.callback_query_handler
		}).run_as_thread()

		try:
			with open(".chats", "r") as f:
				self.chat_id = int(f.readlines()[0].strip())
				print(self.chat_id)
		except FileNotFoundError:
			print("No authenticated chats")
		except Exception as e:
			print(e)
		print("Running bot...")

	def register_chat(self, chat_id):
		with open(".chats", "w") as f:
			f.write(str(chat_id))
			self.chat_id = chat_id
	
	def get_chat_replies(self, msg):
		replies = []
		if msg["text"] == "/start":
			replies.append(("I will notify you when crypto people tweet and give you buying options.", None))
		
		# /orderstatus
		elif msg["text"][:len("/orderstatus")] == "/orderstatus":
			try:
				uuid = msg["text"].split("/orderstatus ")[1].split()[0]
				status = self.bittrex_utils.get_order_status(uuid)
				replies.append((status, None))
			except IndexError:
				replies.append((f'The syntax for this command is "/orderstatus ORDER_UUID"', None))
			except Exception as e:
				raise e
				replies.append((f'An error occurred: {e}', None))
		
		# /cancelorder
		elif msg["text"][:len("/cancelorder")] == "/cancelorder":
			try:
				uuid = msg["text"].split("/cancelorder ")[1].split()[0]
				success = self.bittrex_utils.cancel_order(uuid)
				if not success:
					raise Exception(f'Response returned false')
				replies.append((f'Canceled order {uuid}.', None))
			except IndexError:
				replies.append((f'The syntax for this command is "/cancelorder ORDER_UUID"', None))
			except Exception as e:
				replies.append((f'Could not cancel order {uuid}. (Exception: {e})', None))
		
		# /getopenorders
		elif msg["text"][:len("/getopenorders")] == "/getopenorders":
			try:
				orders = self.bittrex_utils.get_open_orders()
				[replies.append((x, None)) for x in orders]
				if len(orders) == 0:
					replies.append(("No open orders.", None))
			except Exception as e:
				replies.append((f'Could not get orders. (Exception: {e})', None))
		
		# /cancel
		elif msg["text"] == "/cancel" and self.buying:
			self.buying = None
			self.selling = None
			replies.append(("Cancelled order.", None))
		# Buy amount specified
		elif self.buying:
			try:
				amount = float(msg["text"])
				# Create buy order
				pair, quantity, price = self.bittrex_utils.prepare_btc_buy(self.buying, amount)
				
				# Create keyboard options (confirm and cancel)
				# Data scheme - buy:confirm_SYMBOL:amount:pair:quantity:price
				data = [str(x) for x in (amount, pair, quantity, price)]
				buttons = [
					InlineKeyboardButton(text=f'Confirm', callback_data=f'buy:confirm_{self.buying}:{":".join(data)}'),
					InlineKeyboardButton(text=f'Cancel', callback_data=f'buy:cancel_{self.buying}')
				]
				keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
				replies.append((f'Buy {quantity} {self.buying} @ {"{0:.8f}".format(price)} BTC for {amount}', keyboard))
					
			except ValueError as e:
				# Error converting value
				replies.append(("Please enter a valid amount (up to 8 decimal places) e.g.", None))
				replies.append(("0.00000001", None))
			except Exception as e:
				# Exception in bittrex_utils
				replies.append((f'Exception: {e}. Please try again.', None))
		elif self.selling:
			try:
				quantity, price = [float(x) for x in msg["text"].split(",")]
				# Create buy order
				amount = quantity * price
				pair = f'BTC-{self.selling}'

				# Create keyboard options (confirm and cancel)
				# Data scheme - buy:confirm_SYMBOL:btc_amount:pair:quantity:price
				data = [str(x) for x in (amount, pair, quantity, price)]
				buttons = [
					InlineKeyboardButton(text=f'Confirm', callback_data=f'sell:confirm_{self.selling}:{":".join(data)}'),
					InlineKeyboardButton(text=f'Cancel', callback_data=f'sell:cancel_{self.selling}')
				]
				keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
				replies.append((f'Sell {quantity} {self.selling} @ {"{0:.8f}".format(price)} BTC for {amount}', keyboard))
					
			except ValueError as e:
				# Error converting value
				replies.append(("Format: QUANTITY,PRICE e.g. 10000,0.00000050", None))
			except Exception as e:
				# Exception in bittrex_utils
				replies.append((f'Exception: {e}. Please try again.', None))

		return replies

	def get_query_replies(self, query_data, query_id=None):
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
			replies.append((f'Send me an amount in BTC or /cancel ({self.bittrex_utils.get_available_balance("BTC")} BTC available)', None))
		elif query_type == "buy:confirm":
			# Data scheme - buy:confirm_SYMBOL:amount:pair:quantity:price
			coin, amount, pair, quantity, price = [x for x in coin.split(":")]
			amount = float(amount)
			quantity = float(quantity)
			price = float(price)
			
			# Buy
			try:
				uuid = self.bittrex_utils.create_buy_order(pair, quantity, price)
				# Selling option keyboard
				# Data scheme - buy:confirm_SYMBOL:amount:pair:quantity:price
				buttons = [
					InlineKeyboardButton(text=f'Create sell order', callback_data=f'sell_{pair.split("-")[1]}:{uuid}')
				]
				keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

				replies.append((f'Buying {quantity} {coin} @ {"{0:.8f}".format(price)} BTC for total {amount} BTC.\n\nOrder UUID: {uuid}', None))
			except Exception as e:
				replies.append((f'An error ocurred. Please try again (Exception: {e})', None))

			self.buying = None
		elif query_type == "buy:cancel":
			self.buying = None
			replies.append(("Cancelled order.", None))
		elif query_type == "sell":
			try:
				coin, uuid = coin.split(":")
				buy_order = self.bittrex_utils.my_bittrex.get_order(uuid)["result"]
				if not buy_order["IsOpen"]:
					replies.append((f'Send me the quantity and amount of {coin} or /cancel ({self.bittrex_utils.get_available_balance(coin)} {coin} available)\nLast price: {"{0:.8f}".format(self.bittrex_utils.get_last(coin))}\n\nFormat: QUANTITY,PRICE e.g. 10000,0.00000050', None)) 
					self.selling = coin
				else:
					self.bot.answerCallbackQuery(query_id, text='Buy order has not yet completed. Try again.')
			except Exception as e:
				replies.append((f'An error ocurred. (Exception: {e})', None))
		elif query_type == "sell:confirm":
			# Data scheme - sell:confirm_SYMBOL:amount:pair:quantity:price
			coin, amount, pair, quantity, price = [x for x in coin.split(":")]
			amount = float(amount)
			quantity = float(quantity)
			price = float(price)
			
			# Sell
			uuid = self.bittrex_utils.create_sell_order(pair, quantity, price)

			replies.append((f'Selling {quantity} {coin} @ {"{0:.8f}".format(price)} BTC for total {amount} BTC.\n\nOrder UUID: {uuid}', None))
			self.selling = None

		elif query_type == "sell:cancel":
			self.selling = None
			replies.append(("Cancelled order.", None))

		# Answer callback if it hasn't already been answered
		try:
			self.bot.answerCallbackQuery(query_id, text='Got it')
		except:
			pass
			
		return replies

	def chat_handler(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		
		if content_type != "text":
			return

		# Authentication
		if chat_id != self.chat_id:
			if msg["text"] == BOT_TOKEN:
				self.register_chat(chat_id)
				self.bot.sendMessage(chat_id, "Authenticated.")
			else:
				self.bot.sendMessage(chat_id, "Not authenticated. Send me this bot token to authenticate this chat.")
				return

		replies = self.get_chat_replies(msg)

		for reply in replies:
			messsage, keyboard = reply
			self.bot.sendMessage(self.chat_id, messsage, reply_markup=keyboard)

	def callback_query_handler(self, msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor="callback_query")
		
		if not self.chat_id:
			self.bot.sendMessage(chat_id, "Not authenticated. Send me this bot token to authenticate this chat.")
			return

		replies = self.get_query_replies(query_data, query_id=query_id)

		for reply in replies:
			print(reply)
			messsage, keyboard = reply
			self.bot.sendMessage(self.chat_id, messsage, reply_markup=keyboard)
	
	def notify_tweet(self, tweet_text, user, link, to_buy):
		buying_options = [InlineKeyboardButton(text=f'{x[1][0].upper()}{x[1][1:]} ({x[0]})', callback_data=f'summary_{x[0]}') for x in to_buy]
		keyboard = InlineKeyboardMarkup(inline_keyboard=[buying_options])
		message = f'{user}: "{tweet_text}"\n({link})'
		self.bot.sendMessage(self.chat_id, message, reply_markup=keyboard)
