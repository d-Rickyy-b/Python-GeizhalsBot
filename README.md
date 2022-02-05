[![Build Status](https://github.com/d-Rickyy-b/Python-GeizhalsBot/workflows/build/badge.svg?branch=master)](https://github.com/d-Rickyy-b/Python-GeizhalsBot/actions?query=workflow%3Abuild+branch%3Amaster)
[![codecov](https://codecov.io/gh/d-Rickyy-b/Python-GeizhalsBot/branch/master/graph/badge.svg?token=FMP0JX7HKA)](https://codecov.io/gh/d-Rickyy-b/Python-GeizhalsBot)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c923f31dca164626bedb1b21c663cc94)](https://www.codacy.com/manual/d-Rickyy-b/Python-GeizhalsBot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=d-Rickyy-b/Python-GeizhalsBot&amp;utm_campaign=Badge_Grade)

# Python-GeizhalsBot
A bot to get notified about changes of the price of a [geizhals.de](https://geizhals.de) wishlist on Telegram. It uses the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) Framework for talking to Telegram servers.
To get the price of the site it uses pyquery as html parser, since there is no official API for grabbing prices.

## Requirements
This project requires **Python >= 3.6** to run.

## Setup with Docker
The easiest way to get the bot up and running is via Docker. 
Set up a directory with a `config.py` file (you can find an example of it [here](https://github.com/d-Rickyy-b/Python-GeizhalsBot/blob/master/config.sample.py)). If you want to make your logs accessible from the outside, add another volume as follows.

Just run the following command to run the bot:

`docker run -d --name ghbot --restart always -v /path/to/logs/:/usr/src/bot/logs -v /path/to/config.py:/usr/src/bot/config.py geizhalsbot`

Don't forget to **exchange the paths mentioned above** with paths to your config file and logging directory.

## Setup as systemd service

If you don't want to use docker but still want a comfortable way to control the bot, you can create a systemd service.

Create a new file as root in the systemd folder: `/etc/systemd/system/geizhalsbot.service`.
An example systemd configuration can be found in [this GitHub Gist](https://gist.github.com/d-Rickyy-b/6ef4c95bed57da1056e0c696a36e8559). Make sure to change the user and the paths accordingly.

With `systemctl start geizhalsbot` you can start the bot.  
With `systemctl status geizhalsbot` the current status of the service is shown.  
Using `systemctl stop geizhalsbot` you can stop the service,

More on systemd services can be found on the [freedesktop wiki](https://www.freedesktop.org/wiki/Software/systemd/).

## Known-Issues
- The bot is triggered on every change - also if that change is only 0,01€. Later one should be able to set threshold values.
