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

ADMIN_USERS **(MANDATORY)**:
* to use commands in the bot's private chat
* example: ["@username"]

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
5) Make a scheduled message
6) Go to ticket's comments (appears only if discussion chat is connected to your channel)

## User guide
### ***Main channel***

Main channel displays all the tickets you have. In the main channel you have several options to manage your tickets and related information. By writing a message in this channel, it is automatically converted into a ticket with the appropriate tags and buttons. The ticket will be redirected to the specified channel, which is determined based on name and priority.

In the main channel you can perform the following actions with the ticket:
* Open/close ticket: change the ticket status to open or closed
* Reassign the ticket to another channel: you can reassign the main user behind the ticket to another channel
* Change the users following the ticket: you can change the list of users following the ticket
* Change the priority of the ticket: you can change the priority level of the ticket
* Scheduled message: You can select a date and time, then the ticket will change its tag and move to the pending message channel for each tracked user. After a specified time, the message will be removed from the reserved message channel and delivered to specific users
* Go to Ticket Comments: If your channel has a discussion chat, a button will be available that allows you to go directly to the comment section of the ticket. This simplifies discussion and collaboration related to the ticket. (You can add a channel for discussion in the main channel settings)

The same steps can be performed in the channel for users and the channel for scheduled messages.

### ***Chat commands for customization***

If you go into chat with the bot and enter the command "/help", you will get a list of available commands. I will now list these commands for you.

Changes dump chat id:
* /set_dump_chat_id (CHAT_ID)
* Example: /set_dump_chat_id -1001234123412

Changes delay between interval checks:
* /set_interval_check_time (MINUTES)
* Example: /set_interval_check_time 60

Add main channel:
* /add_main_channel (CHANNEL_ID)
* Example: /add_main_channel -100987987987

Remove main channel:
* /remove_main_channel (CHANNEL_ID)
* Example: /remove_main_channel  -100987987987

Enables auto forwarding tickets found during scanning:
* /enable_auto_forwarding

Disables auto forwarding tickets found during scanning:
* /disable_auto_forwarding

Changes timezone identifier:
* /set_timezone (TIMEZONE) 
* Example: /set_timezone Europe/Kiev

Add subchannel to main channel with specified tag and priority:
* /set_subchannel (MAIN_CHANNEL_ID) (TAG) (PRIORITY) (SUBCHANNEL_ID)
* Example: /set_subchannel -100987987987 aa 1 -100123321123

Removes all subchannels with specified tag in main channel:
* /remove_subchannel_tag (MAIN_CHANNEL_ID) (TAG)
* Example: /remove_subchannel_tag -100987987987 aa

Add or change username or user id of the tag:
* /set_user_tag (MAIN_CHANNEL_ID) (TAG) (USERNAME_OR_USER_ID)
* Example with username: /set_user_tag -100987987987 aa @username
* Example with user id: /set_user_tag -100987987987 aa 321123321

Remove user assigned to specified tag:
* /remove_user_tag (MAIN_CHANNEL_ID) (TAG)
* Example with username: /remove_user_tag -100987987987 aa

Changes default subchannel:
* /set_default_subchannel (MAIN_CHANNEL_ID) (DEFAULT_USER_TAG) (DEFAULT_PRIORITY)
* Example: /set_user_tag -100987987987 aa 1

Changes storage channel for scheduled messages:
* /set_storage_channel (MAIN_CHANNEL_ID) (STORAGE_CHANNEL_ID) (TAG)
* Example: /set_storage_channel -100987987987 -100432423423 aa

Changes storage channel for scheduled messages:
* /set_button_text (BUTTON_NAME) (NEW_VALUE)
* Available buttons: opened, closed, assigned, cc, schedule, check, priority
* Example: /set_button_text opened 🟩
* /set_button_text priority - 1 2 3

Changes storage channel for scheduled messages:
* /set_hashtag_text (HASHTAG_NAME) (NEW_VALUE)
* Available hashtags: opened, closed, scheduled, priority
* Example: /set_hashtag_text opened Op

### ***Deleting messages from user channels***

When closing a ticket (by pressing the "close ticket" button), if the ticket has been in the channel for less than 48 hours, the ticket will be deleted from that channel.

But if the ticket is more than 48 hours old, the ticket will be deleted from the channel and will go to the very beginning of the channel with the "to_delete" tag, this message can then be deleted manually.

All closed tickets remain in the main channel and can be reopened.
