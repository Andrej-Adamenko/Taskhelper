import json
import logging
import os
import sys

import telebot

CONFIG_FILE = "config.json"

if not os.path.exists(CONFIG_FILE):
	logging.error("Config file not found")
	exit()

MANDATORY_KEYS = ["BOT_TOKEN", "DUMP_CHAT_ID"]

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
DELAY_AFTER_ONE_SCAN = 4

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
		current_config[config_key] = updated_config_data[config_key]

	with open(CONFIG_FILE, "w", encoding="utf-8") as f:
		json.dump(current_config, f, indent=4, ensure_ascii=False)


