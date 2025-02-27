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

APP_API_ID **(MANDATORY)**:
* app id of your telegram application, needed for exporting comments from discussion chat 
* example: 12345

APP_API_HASH **(MANDATORY)**:
* app hash of your telegram application, needed for exporting comments from discussion chat 
* example: "42f28ff2118430bdff5f9a189e0034ec"

DEFAULT_USER_DATA:
* name and priority of a channel that messages forwarded to by default
* example: "ak 1"

UPDATE_INTERVAL:
* interval(in minutes) between regular ticket checking
* example: 60

INTERVAL_UPDATE_START_DELAY:
* delay(in seconds) before start of an interval check since bot was started
* example: 60

MAX_BUTTONS_IN_ROW:
* max amount of buttons in one row, won't affect control buttons
* example: 3

DELAY_AFTER_ONE_SCAN:
* delay(in seconds) before next message check during interval checking
* example: 5

TIMEZONE_NAME:
* timezone for deferred messages
* example: "Europe/Kiev"

## FAQ
How to create bot and get bot token:
* Find @BotFather in Telegram and text to him `/newbot` 

What is dump chat:
* This is chat that bot will have to use when he needs to read a message, he will forward message there to obtain message content and then delete it

What is ticket's followed users:
* If ticket have more than one user assigned than ticket will be forwarded to all of them

How to get chat id of a channel or chat:
1) Right click on any post in the channel
2) In the opened menu select "Copy Post Link" or "Copy Message Link"
3) After that you will have a link in your clipboard, example: "https://t.me/c/2497828750/123"
4) You should copy the first number from this link, in this example it will be 2497828750
5) Insert -100 before the number that you copied before, in this example final chat id will be -1002497828750

## How to run
When you installed Python, dependencies and filled config.json you should invite bot to your channels(dump chat, main channel, all subchannels) and run:
```
$ python3 main.py
```

You can also execute tests with
```
$ python3 -m unittest -v
```

In order for bot to be able to forward tickets to subchannels you need to specify hashtags in the text of your ticket:
* #о - means ticket is open and bot can forward it to subchannel
* #х - means ticket is closed
* #ak - user's name of a subchannel, instead of "ak" you should specify name that you put in config file, multiple user can be assigned to one ticket 
* #п1 - ticket priority, instead of "1" you can specify ticket's priority

You can also change ticket's tags using buttons that bot will add to all messages in main channel

## How to create a service
If you want the bot to be always running you can create a service that will automatically start the bot with the system startup.

In order to create the service first you should create a service file which will contain a configuration for your service. It should be placed in **/etc/systemd/system**, the name of the file will be the name of your service, and have **.service** extension, example:
```
/etc/systemd/system/taskhelper.service
```

Here is an example of a service file content:
```
[Unit]
Description=Taskhelper service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/taskhelper_user/Taskhelper/main.py
WorkingDirectory=/home/user/Taskhelper
RestartSec=30
Restart=always
User=taskhelper_user

[Install]
WantedBy=multi-user.target
```

You need to change **ExecStart**, **WorkingDirectory** and **User**, other options can remain the same.

After service file is created you need to run following commands.
```
systemctl enable taskhelper.service
systemctl start taskhelper.service
```

After that bot will be started, and when the system is turned on it will automatically start the bot.

## Buttons
There are 5 control buttons:
1) Open/close ticket
2) Reassign ticket to different subchannel
3) Change ticket's followed users
4) Change ticket's priority
5) Make a deferred message
6) Go to ticket's comments (appears only if discussion chat is connected to your channel)

## User guide
### ***Main channel***

Main channel displays all the tickets you have. In the main channel you have several options to manage your tickets and related information. By writing a message in this channel, it is automatically converted into a ticket with the appropriate tags and buttons. The ticket will be redirected to the specified channel, which is determined based on name and priority.

In the main channel you can perform the following actions with the ticket:
* Open/close ticket: change the ticket status to open or closed
* Reassign the ticket to another channel: you can reassign the main user behind the ticket to another channel
* Change the users following the ticket: you can change the list of users following the ticket
* Change the priority of the ticket: you can change the priority level of the ticket
* Deferred message: You can select a date and time, then the ticket will change its tag and move to the pending message channel for each tracked user. After a specified time, the message will be removed from the reserved message channel and delivered to specific users
* Go to Ticket Comments: If your channel has a discussion chat, a button will be available that allows you to go directly to the comment section of the ticket. This simplifies discussion and collaboration related to the ticket. (You can add a channel for discussion in the main channel settings)

The same steps can be performed in the channel for users and the channel for deferred messages.

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

Changes timezone identifier:
* /set_timezone (TIMEZONE) 
* Example: /set_timezone Europe/Kiev

Add or change username or user id of the tag:
* /set_user_tag (MAIN_CHANNEL_ID) (TAG) (USERNAME_OR_USER_ID)
* Example with username: /set_user_tag -100987987987 aa @username
* Example with user id: /set_user_tag -100987987987 aa 321123321

Remove user assigned to specified tag:
* /remove_user_tag (MAIN_CHANNEL_ID) (TAG)
* Example with username: /remove_user_tag -100987987987 aa

Changes default user and priority:
* /set_default_subchannel (MAIN_CHANNEL_ID) (DEFAULT_USER_TAG) (DEFAULT_PRIORITY)
* Example: /set_default_subchannel -100987987987 aa 1

Changes button text:
* /set_button_text (BUTTON_NAME) (NEW_VALUE)
* Available buttons: opened, closed, assigned, cc, defer, check, priority
* Example: /set_button_text opened OPEN
* Priority button text will have 4 values, first for missing priority and 3 others for each priority, for example: /set_button_text priority NO_PRIORITY FIRST SECOND THIRD

Changes the text of the service hashtags:
* /set_hashtag_text (HASHTAG_NAME) (NEW_VALUE)
* Available hashtags: opened, closed, deferred, priority
* Example: /set_hashtag_text opened Op
* Important: after this is executed the bot will start interval update to replace every old hashtag with the new hashtag 

Changes timeout for skipping daily reminder if user is interacted with tickets within this time:
* /set_remind_without_interaction (MINUTES)
* Example: /set_remind_without_interaction 1440

### ***Individual channel structure for every user***

Each created channel now has its own unique structure. After adding a bot to a new channel, simply write "/start" to bring up the settings menu.

The settings menu gives you the option to select or deselect certain settings from the nine available:

* "Assigned to" - include tickets that is assigned to the selected users.
* "Reported by" - include tickets that is created by the selected users.
* "CCed to" - include tickets where the selected users in CC.
* "Remind me when" - regulates what tickets can be reminded in this channel.
* "Due" - if this option is enabled, regular(NOT deferred) tickets and also tickets deferred until a date, but that date is in the past now, will all be included in this channel.
* "Deferred" - if this option is enabled, tickets, deferred until now will be included in this channel.
* "Priority 1/2/3" - here you should specify which tickets with priority 1, 2 and 3 will be forwarded to this channel.

The "Assigned to", "Reported by", and "CCed to" buttons open a menu of user tags where multiple user tags can be selected at once.

Selected users are displayed in the button text as "Assigned to: aa, bb, cc".

In addition to user tags, there is also a "New User" option that will automatically add new users to the current category after they have been added using the bot command.

"Due" and "Deferred" by default, both parameters are ON when a new channel is created.

After selecting the desired settings, you should press the "Save" button to save and apply the settings.

You can open this menu by pressing "Settings ⚙️" button on the last ticket in channel or by pressing "Edit channel settings ⚙️" button on the message with current channel settings.

If you want redirect to the message with current channel settings, you can press the "Help" button in the settings menu on the last ticket.

If message with "Edit channel settings ⚙️" was deleted you can use "/settings" command to create it again.

### ***Custom hashtags for specific channels***

You can create your own "hashtags" for certain channels.

To do this, go to the user channel and use the command "/set_channel_hashtag" specifying the desired hashtag, for example, "/set_channel_hashtag #test". 

After the hashtag is set, to move a ticket from the main channel to a certain channel, you should specify the corresponding hashtag in the ticket body.

### ***Add last comment to ticket's body***

You can add your own comments to each ticket. 

To do this, go to the comments section for a particular ticket, accessible via button number 6. 

Then, in the input field, write a comment, starting it with ":". For example, ":test_comment". This comment will appear in the body of the ticket after the "::" character.

You can add a comment by editing the ticket using the "Edit" button (by right-clicking on the ticket) and add a comment starting with the "::" character. For example, "::test_comment".

If you want to change the comment, use the ":" symbol via button number 6 and write your corrected comment.

In addition you can edit the comment using the "Edit" button (by pressing the right button on the ticket).

You can also delete a comment via "Edit" (by right-clicking on the ticket).

### ***Deleting messages from user channels***

When closing a ticket (by pressing the "close ticket" button), if the ticket has been in the channel for less than 48 hours, the ticket will be deleted from that channel.

But if the ticket is more than 48 hours old, the ticket will be deleted from the channel and will go to the very beginning of the channel with the "to_delete" tag, this message can then be deleted manually.

All closed tickets remain in the main channel and can be reopened.

