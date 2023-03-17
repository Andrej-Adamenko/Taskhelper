import json, logging, os

def load_config(config_filename):
	if not os.path.exists(config_filename):
		logging.error("Config file not found")
		exit()

	f = open(config_filename, "r")
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
		config_json["SUBCHANNEL_DATA"] = []	

	config_data_list = []
	config_data_list.append(config_json["BOT_TOKEN"])
	config_data_list.append(config_json["CHANNEL_IDS"])
	config_data_list.append(config_json["DUMP_CHAT_ID"])
	config_data_list.append(config_json["SUBCHANNEL_DATA"])

	return config_data_list

def update_config(updated_config_data, config_filename):
	if not os.path.exists(config_filename):
		logging.error("Config file not found")
		exit()

	f = open(config_filename, "r")
	config_json = json.load(f)
	f.close()

	for config_key in updated_config_data:
		config_json[config_key] = updated_config_data[config_key]

	f = open(config_filename, "w")
	json.dump(config_json, f)
	f.close()
