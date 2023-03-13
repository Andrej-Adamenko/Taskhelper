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

After that you should create config.json file and fill-in your bot token and channel id.
Example of config.json:
```
{
	"BOT_TOKEN": "1234567890:ABCD12345-ABCD124567ASD-BB",
	"CHANNEL_IDS": [-1001234567890]
}
```

## FAQ
How to create bot and get bot token:
* Find @BotFather in Telegram and text to him `/newbot` 

How to get channel_id of my channel:
* Find @RawDataBot in Telegram and forward him any message from you channel.
* In response message you need to find `forward from_chat` block, in `id` field you'll find your channel_id , example:
```
"forward_from_chat": {
    "id": -1001234567890,
    "title": "TChannel",
    "type": "channel"
}
```  

## How to run
When you installed Python, dependencies and filled config.json you should invite bot into your channel and run:
```
$ python3 main.py
```