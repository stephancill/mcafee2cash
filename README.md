# mcafee2cash
* Listen for tweets from @JohnMcAfee
* Check if tweet contains a symbol listed on Bittrex
* Analyze sentiment
* Buy on Bittrex if good (TODO)*
* Sell 24 hours later (TODO)*

***Available on `dev` branch**

APIs used:
* Twitter (tweepy)
* Telegram (telepot)
* Bittrex (python-bittrex)

If you get stuck, don't hesitate to open an issue or message me on Twitter [@stephancill](https://twitter.com/stephancill)

## How it works
A stream is configured to listen to new tweets by user IDs specified in `config.json`. When it receives a tweet, it checks if any coins that trade on Bittrex are mentioned, analyzes the overall sentiment and determines which coins you should buy. The Telegram bot then sends you a message with those buying options and allows you to inspect a market summary of all the buying options. Along with the market summary, it provides you with a button that you can press to buy the coin on Bittrex and asks you to specify how much (in BTC) you would like to spend and places a buy order at the asking price.

## Requirements
* Python 3.6
* [pipenv](https://github.com/pypa/pipenv)

## Setup
1. `git clone https://github.com/stephancill/mcafee2cash.git`
2. `cd mcafee2cash`
3. `pipenv install --three` (if this fails, delete `Pipfile.lock` and try again)
4. `pipenv run "python -m textblob.download_corpora"` to download sentiment analysis dependencies
5. Populate `secrets.json`
6. Modify `config.json` (optional)

### `secrets.json` info
* Bittrex - Create a [Bittrex](https://bittrex.com/Manage#sectionApi) API key with `READ INFO,	TRADE LIMIT,	TRADE MARKET` permissions
* Telegram - Create a bot by talking to [@BotFather](http://t.me/botfather)
* Twitter - Create a new Twitter app at https://apps.twitter.com/app/new

## Usage
1. Start the service using `pipenv run python main.py`
2. Send your bot token to the bot to authenticate your chat
3. Wait for McAfee to pump a coin

## Contributing
Contributions welcome. Open a pull request!

## License
MIT License
