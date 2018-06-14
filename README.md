[![Build Status](https://travis-ci.org/d-Rickyy-b/Python-GeizhalsBot.svg?branch=master)](https://travis-ci.org/d-Rickyy-b/Python-GeizhalsBot) [![Coverage Status](https://coveralls.io/repos/github/d-Rickyy-b/Python-GeizhalsBot/badge.svg?branch=master)](https://coveralls.io/github/d-Rickyy-b/Python-GeizhalsBot?branch=master)

# Python-GeizhalsBot
A bot to get notified about changes of the price of a Geizhals.de wishlist on Telegram. It uses the [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot) Framework for talking to Telegram servers.
To get the price of the site it uses pyquery as html parser, since there is no official API for grabbing prices.

### Known-Issues
- The bot can currently only fetch prices for wishlists. Later it should be able to track prices of single items.
- The bot is triggered on every change - also if that change is only 0,01€. Later one should be able to set threshold values.
