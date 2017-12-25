from bittrex.bittrex import Bittrex
import json
import requests

with open("secrets.json") as f:
	keys = json.load(f)
	BITTREX_KEY = keys["BITTREX_KEY"]
	BITTREX_SECRET = keys["BITTREX_SECRET"]

def summary_bittrex(coin):
	pair = f'BTC-{coin}'
	url = f'https://bittrex.com/api/v1.1/public/getmarketsummary?market={pair}'
	response = requests.request("GET", url)
	resp = response.json()
	if not resp["success"]:
		raise Exception(f'Bittrex: {resp["message"]} (Pair: {pair})')

	summary = {
		"endpoint"  :   url,
		"bid"       :   '{0:.8f}'.format(float(resp["result"][0]["Bid"])),
		"ask"       :   '{0:.8f}'.format(float(resp["result"][0]["Ask"])),
		"last"      :   '{0:.8f}'.format(float(resp["result"][0]["Last"])),
		"volume"    :   float(resp["result"][0]["BaseVolume"]),
		"yesterday" :   '{0:.8f}'.format(float(resp["result"][0]["PrevDay"]))
	}
	last = float(resp["result"][0]["Last"])
	yesterday = float(resp["result"][0]["PrevDay"])
	summary["change"] = round((last - yesterday)/((last + yesterday)/2) * 10**4)/10**2

	return summary

class BittrexUtils:
	def __init__(self):
		self.my_bittrex = Bittrex(BITTREX_KEY, BITTREX_SECRET)
	
	def get_available_balance(self, symbol):
		return self.my_bittrex.get_balance(symbol)["result"]["Available"]

	def get_ask(self, symbol):
		"""Return current ask price for symbol"""
		pair = f'BTC-{symbol}'
		return self.my_bittrex.get_marketsummary(pair)["result"][0]["Ask"]

	def get_bid(self, symbol):
		"""Return current bid price for symbol"""
		pair = f'BTC-{symbol}'
		return self.my_bittrex.get_marketsummary(pair)["result"][0]["Bid"]

	def get_last(self, symbol):
		"""Return current last price for symbol"""
		pair = f'BTC-{symbol}'
		return self.my_bittrex.get_marketsummary(pair)["result"][0]["Last"]

	def prepare_btc_buy(self, symbol, amount):
		"""Prepare get pair, quantity and price for create_buy_order"""
		pair = f'BTC-{symbol}'
		price = self.get_ask(symbol) * 1.02 # Buy 2% higher
		quantity = round(amount/price, 8)
		return pair, quantity, price

	def create_buy_order(self, pair, quantity, price):
		"""Create buy order on Bittrex, return order uuid"""
		response = self.my_bittrex.buy_limit(pair, quantity, price)
		if response["success"]:
			return response["result"]["uuid"]
		else:
			raise Exception(response["message"])

	def create_sell_order(self, pair, quantity, price):
		"""Create sell order on Bittrex, return order uuid"""
		response = self.my_bittrex.sell_limit(pair, quantity, price)
		if response["success"]:
			return response["result"]["uuid"]
		else:
			raise Exception(response["message"])
	
	def get_open_orders(self):
		orders = self.my_bittrex.get_open_orders()["result"]
		result = []
		for order in orders:
			message = f'Order {order["OrderUuid"]}\n\n{order["Exchange"]}\nType: {order["OrderType"]}\nQuantity: {order["Quantity"]}\nPrice: {order["Limit"]}\nBTC total: {order["Limit"]*order["Quantity"]}\n\nOpen: {order["Closed"] == None}'
			result.append(message)
		return result

	def cancel_order(self, uuid):
		return self.my_bittrex.cancel(uuid)["success"]
	
	def get_order_status(self, uuid):
		"""Returns string of order status"""
		order = self.my_bittrex.get_order(uuid)["result"]
		return f'Order {order["OrderUuid"]}\n\n{order["Exchange"]}\nType: {order["Type"]}\nQuantity: {order["Quantity"]}\nPrice: {order["Limit"]}\nBTC total: {order["Reserved"]}\n\nOpen: {order["IsOpen"]}'

if __name__ == "__main__":
	trex = BittrexUtils()
	print(trex.get_order_status("e0ad333f-dc9a-4d8c-ae7e-e65f5ac223cc"))