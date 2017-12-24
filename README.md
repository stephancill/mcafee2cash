# mcafee2cash
Listens for tweets on Twitter, parses them and identifies sentiment, communicates back to you via Telegram bot and provides buying functionality that interfaces with the Bittrext public API.

## Setup
1. `git clone https://github.com/stephancill/mcafee2cash.git`
2. `cd mcafee2cash`
3. `pipenv install`
4. Populate `secrets.json`
5. `pipenv run python main.py`

### `secrets.json`
* Bittrex - Create a [Bittrex](https://bittrex.com/Manage#sectionApi) API key with `READ INFO,	TRADE LIMIT,	TRADE MARKET` permissions
* Telegram - Create a bot by talking to [@BotFather](http://t.me/botfather)
* Twitter - Create a new Twitter app at https://apps.twitter.com/app/new