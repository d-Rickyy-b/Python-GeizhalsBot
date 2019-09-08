[![Build Status](https://travis-ci.org/d-Rickyy-b/Python-GeizhalsBot.svg?branch=master)](https://travis-ci.org/d-Rickyy-b/Python-GeizhalsBot) [![Coverage Status](https://coveralls.io/repos/github/d-Rickyy-b/Python-GeizhalsBot/badge.svg?branch=master)](https://coveralls.io/github/d-Rickyy-b/Python-GeizhalsBot?branch=master)

# Python-GeizhalsBot
A bot to get notified about changes of the price of a Geizhals.de wishlist on Telegram. It uses the [Python-Telegram-Bot](https://github.com/python-telegram-bot/python-telegram-bot) Framework for talking to Telegram servers.
To get the price of the site it uses pyquery as html parser, since there is no official API for grabbing prices.

### Requirements
The GeizhalsBot requires **Python > 3.4** to run. Python 3.4 has reached end-of-life. Make sure to use Python 3.5 or later, otherwise you will run into issues.

### Setup with Docker
The easiest way to get the bot up and running is via docker. 
Setup a directory with a `config.py` file (you can find an example of it [here](https://github.com/d-Rickyy-b/Python-GeizhalsBot/blob/master/config.sample.py)). If you want to make your logs accessible from the outside, add another volume as follows.

Just run the following command to run the bot:

`docker run -d --name ghbot --restart always -v /path/to/logs/:/usr/src/bot/logs -v /path/to/config.py:/usr/src/bot/config.py geizhalsbot`

Don't forget to **exchange the paths mentioned above** with paths to your config file and logging directory.

### Setup as systemd service

If you don't want to use docker but still want a comfortable way to control the bot, you can create a systemd service.

Create a new file as root in the systemd folder: `/etc/systemd/system/geizhalsbot.service`.
An example systemd configuration can be found in [this GitHub Gist](https://gist.github.com/d-Rickyy-b/6ef4c95bed57da1056e0c696a36e8559). Make sure to change the user and the paths accordingly.


With `systemctl start geizhalsbot` you can start the bot.  
With `systemctl status geizhalsbot` the current status of the service is shown.  
Using `systemctl stop geizhalsbot` you can stop the service,

More on systemd services can be found on the [freedesktop wiki](https://www.freedesktop.org/wiki/Software/systemd/).

### Known-Issues
- The bot is triggered on every change - also if that change is only 0,01€. Later one should be able to set threshold values.
