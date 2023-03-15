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

After that you should create config.json file and fill-in your bot token.
Example of config.json:
```
{
	"BOT_TOKEN": "1234567890:ABCD12345-ABCD124567ASD-BB"
}
```

## FAQ
How to create bot and get bot token:
* Find @BotFather in Telegram and text to him `/newbot` 

## How to run
When you installed Python, dependencies and filled config.json you should invite bot into your channel and run:
```
$ python3 main.py
```

Bot will start working right after you add him to your channel.
