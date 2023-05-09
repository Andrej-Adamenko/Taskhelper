import json
import logging
import os
import sys
import typing

import telebot

CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
	logging.error("Config file not found")
	exit()

MANDATORY_KEYS = ["BOT_TOKEN", "ADMIN_USERS"]

BOT_TOKEN: str = ""
DUMP_CHAT_ID: str = ""
CHANNEL_IDS: list = []
SUBCHANNEL_DATA: dict = {}
DISCUSSION_CHAT_DATA: dict = {}
DEFAULT_USER_DATA: dict = {}
UPDATE_INTERVAL: int = 60
INTERVAL_UPDATE_START_DELAY: int = 10
AUTO_FORWARDING_ENABLED: bool = False
MAX_BUTTONS_IN_ROW: int = 3
DELAY_AFTER_ONE_SCAN: int = 4
SUPPORTED_CONTENT_TYPES: list = ["audio", "photo", "voice", "video", "document", "text"]
APP_API_ID: int = 0
APP_API_HASH: str = ""
EXPORTED_DISCUSSION_CHATS: list = []
SCHEDULED_STORAGE_CHAT_IDS: dict = {}
TIMEZONE_NAME: str = "UTC"
USER_DATA: dict = {}
ADMIN_USERS: list = []
BUTTON_TEXTS: dict = {
	"OPENED_TICKET": "\U0001F7E9",
	"CLOSED_TICKET": "\U00002705",
	"ASSIGNED_USER_PREFIX": "➔",
	"CC": "CC",
	"SCHEDULE_MESSAGE": "\U0001f552",
	"CHECK": "\U00002705",
	"PRIORITIES": {
		"-": "\u26a0?",
		"1": "\u0031\uFE0F\u20E3",
		"2": "\u0032\uFE0F\u20E3",
		"3": "\u0033\uFE0F\u20E3"
	}
}

HASHTAGS: dict = {
	"OPENED": "о",
	"CLOSED": "х",
	"SCHEDULED": "з",
	"PRIORITY": "п",
}

HASHTAGS_BEFORE_UPDATE: typing.Optional[dict] = None

BOT_ID: int = 0
CHAT_IDS_TO_IGNORE: list = []

config_json = {}
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
	config_json = json.load(f)

for mandatory_key in MANDATORY_KEYS:
	if mandatory_key not in config_json:
		logging.error(f"{mandatory_key} not declared in config file")
		exit()

this_module = sys.modules[__name__]
for key in config_json:
	setattr(this_module, key, config_json[key])


def load_discussion_chat_ids(bot: telebot.TeleBot):
	for channel_id in CHANNEL_IDS:
		channel_data = bot.get_chat(channel_id)
		DISCUSSION_CHAT_DATA[str(channel_id)] = channel_data.linked_chat_id


def update_config(updated_config_data):
	if not os.path.exists(CONFIG_FILE):
		logging.error("Config file not found")
		exit()

	current_config = {}
	with open(CONFIG_FILE, "r", encoding="utf-8") as f:
		current_config = json.load(f)

	for config_key in updated_config_data:
		if updated_config_data[config_key] is None:
			if config_key in current_config:
				del current_config[config_key]
			continue
		current_config[config_key] = updated_config_data[config_key]

	with open(CONFIG_FILE, "w", encoding="utf-8") as f:
		json.dump(current_config, f, indent=4, ensure_ascii=False)


def load_users(bot: telebot.TeleBot):
	for main_channel_id in USER_DATA:
		for user_tag in USER_DATA[main_channel_id]:
			user_id = USER_DATA[main_channel_id][user_tag]
			if type(user_id) != int:
				continue
			try:
				user_info = bot.get_chat(user_id)
			except Exception as E:
				logging.error(f"Error during loading info about user {user_id}, {E}")
				continue
			if user_info:
				USER_DATA[main_channel_id][user_tag] = user_info

