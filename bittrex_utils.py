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
	
	def get_available_balance(self):
		return self.my_bittrex.get_balance("BTC")["result"]["Balance"]

	def get_ask(self, symbol):
		pair = f'BTC-{symbol}'
		return self.my_bittrex.get_marketsummary(pair)["result"][0]["Ask"]

	def get_bid(self, symbol):
		pair = f'BTC-{symbol}'
		return self.my_bittrex.get_marketsummary(pair)["result"][0]["Bid"]

	def buy_in_btc(self, symbol, amount):
		pair = f'BTC-{symbol}'
		ask = self.get_ask(symbol)
		quantity = amount/ask
		return pair, ask, round(quantity, 8)
		# return self.my_bittrex.buy_limit(pair, quantity, ask)


if __name__ == "__main__":
	utils = BittrexUtils()
	# print(utils.buy_in_btc("doge", 0.01))
