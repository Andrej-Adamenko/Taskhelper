## Taskhelper

Telegram bot for managing tasks in channels.

## Installation
First you need to install Python 3.7+. 
You can download Taskhelper using git:
```
$ git clone https://github.com/DnRuban/Taskhelper.git
```

Than install dependencies using pip:
```
cd Taskhelper
$ pip install -r requirements.txt
```

After that you should create config.json file and fill-in your bot token and dump chat id.
Example of config.json:
```
{
	"BOT_TOKEN": "1234567890:ABCD12345-ABCD124567ASD-BB",
    "DUMP_CHAT_ID": -100123456789
}
```

## Config file options
You need to specify only mandatory fields, other options have default values 

BOT_TOKEN **(MANDATORY)**:
* bot token for accessing telegram bot api
* example: "1234567890:ABCD12345-ABCD124567ASD-BB"

DUMP_CHAT_ID **(MANDATORY)**:
* chat id for forwarding messages when bot needs to read them
* example: -1001234123412

CHANNEL_IDS:
* chat ids of main channels where tickets will be created and managed
* example: [-100123123123, -100456456456]

SUBCHANNEL_DATA:
* data for forwarding tickets to channels
* structure: "MAIN_CHANNEL_ID": {"NAME": {"PRIORITY": SUBCHANNEL_ID, "PRIORITY": SUBCHANNEL_ID, ...} 
* example: "-100123123123": {"ak": {"1": -100345345345, "2": -100567567567, "3": -100678678678}}

DEFAULT_USER_DATA:
* name and priority of a channel that messages forwarded to by default
* example: "ak 1"

UPDATE_INTERVAL:
* interval(in minutes) between regular ticket checking
* example: 60

INTERVAL_UPDATE_START_DELAY:
* delay(in seconds) before start of an interval check since bot was started
* example: 60

AUTO_FORWARDING_ENABLED:
* if true during interval checks bot will automatically forward tickets to subchannels 
* example: false

MAX_BUTTONS_IN_ROW:
* max amount of buttons in one row, won't affect control buttons
* example: 3

DELAY_AFTER_ONE_SCAN:
* delay(in seconds) before next message check during interval checking
* example: 5

APP_API_ID:
* app id of your telegram application, needed for exporting comments from discussion chat 
* example: 12345

APP_API_HASH:
* app hash of your telegram application, needed for exporting comments from discussion chat 
* example: "42f28ff2118430bdff5f9a189e0034ec"

TIMEZONE_NAME:
* timezone for scheduled messages
* example: "Europe/Kiev"

SCHEDULED_STORAGE_CHAT_IDS:
* data about storage channels for scheduled messages, keys are main channel ids, values are storage channel ids 
* example: {"-1001234234134": -1001234234134}

## FAQ
How to create bot and get bot token:
* Find @BotFather in Telegram and text to him `/newbot` 

What is dump chat:
* This is chat that bot will have to use when he needs to read a message, he will forward message there to obtain message content and then delete it

What is ticket's followed users:
* If ticket have more than one user assigned than ticket will be forwarded to all of them

## How to run
When you installed Python, dependencies and filled config.json you should invite bot to your channels(dump chat, main channel, all subchannels) and run:
```
$ python3 main.py
```

In order for bot to be able to forward tickets to subchannels you need to specify hashtags in the text of your ticket:
* #о - means ticket is open and bot can forward it to subchannel
* #х - means ticket is closed
* #ak - user's name of a subchannel, instead of "ak" you should specify name that you put in config file, multiple user can be assigned to one ticket 
* #п1 - ticket priority, instead of "1" you can specify ticket's priority

You can also change ticket's tags using buttons that bot will add to all messages in main channel

## Buttons
There are 5 control buttons:
1) Open/close ticket
2) Reassign ticket to different subchannel
3) Change ticket's followed users
4) Change ticket's priority
5) Go to ticket's comments (appears only if discussion chat is connected to your channel)

