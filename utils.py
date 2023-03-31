import json
import logging
import os

CONFIG_FILE = "config.json"


def load_config():
	if not os.path.exists(CONFIG_FILE):
		logging.error("Config file not found")
		exit()

	f = open(CONFIG_FILE, "r", encoding="utf-8")
	config_json = json.load(f)
	f.close()

	if "BOT_TOKEN" not in config_json:
		logging.error("Bot token not found in config file")
		exit()

	if "DUMP_CHAT_ID" not in config_json:
		logging.error("Dump chat id not found in config file")
		exit()

	if "CHANNEL_IDS" not in config_json:
		config_json["CHANNEL_IDS"] = []

	if "SUBCHANNEL_DATA" not in config_json:
		config_json["SUBCHANNEL_DATA"] = {}

	if "DISCUSSION_CHAT_DATA" not in config_json:
		config_json["DISCUSSION_CHAT_DATA"] = {}

	if "DEFAULT_USER_DATA" not in config_json:
		config_json["DEFAULT_USER_DATA"] = {}

	if "UPDATE_INTERVAL" not in config_json:
		config_json["UPDATE_INTERVAL"] = 60

	if "INTERVAL_UPDATE_START_DELAY" not in config_json:
		config_json["INTERVAL_UPDATE_START_DELAY"] = 10

	config_data_list = [
		config_json["BOT_TOKEN"],
		config_json["CHANNEL_IDS"], config_json["DUMP_CHAT_ID"],
		config_json["SUBCHANNEL_DATA"],
		config_json["DISCUSSION_CHAT_DATA"],
		config_json["DEFAULT_USER_DATA"],
		config_json["UPDATE_INTERVAL"],
		config_json["INTERVAL_UPDATE_START_DELAY"]
	]

	return config_data_list


def update_config(updated_config_data):
	if not os.path.exists(CONFIG_FILE):
		logging.error("Config file not found")
		exit()

	f = open(CONFIG_FILE, "r")
	config_json = json.load(f)
	f.close()

	for config_key in updated_config_data:
		config_json[config_key] = updated_config_data[config_key]

	f = open(CONFIG_FILE, "w")
	json.dump(config_json, f, indent=4, ensure_ascii=False)
	f.close()


def create_callback_str(callback_prefix, callback_type, *args):
	arguments_str = ",".join([str(arg) for arg in args])
	components = [callback_prefix, callback_type]
	if arguments_str:
		components.append(arguments_str)
	callback_str = ",".join(components)
	return callback_str


def offset_entities(entities, offset):
	if not entities:
		return []

	for entity in entities:
		entity.offset += offset

	return entities


def get_forwarded_from_id(message_data):
	if message_data.forward_from_chat:
		return message_data.forward_from_chat.id
	if message_data.forward_from:
		return message_data.forward_from.id

	return None


BOT_TOKEN, CHANNEL_IDS, DUMP_CHAT_ID, SUBCHANNEL_DATA, DISCUSSION_CHAT_DATA, DEFAULT_USER_DATA, UPDATE_INTERVAL, INTERVAL_UPDATE_START_DELAY = load_config()

