import json, logging

def load_config(config_filename):
	f = open(config_filename, "r")
	config_json = json.load(f)
	f.close()

	if "BOT_TOKEN" not in config_json:
		logging.error("Bot token not found in config file")
		exit()

	config_data_list = []
	config_data_list.append(config_json["BOT_TOKEN"])

	if "CHANNEL_IDS" in config_json:
		config_data_list.append(config_json["CHANNEL_IDS"])
	else:
		config_data_list.append([])

	return config_data_list

def get_post_url(post_data):
	channel_url = str(post_data.chat.id)[4:]
	return "https://t.me/c/{0}/{1}".format(channel_url, post_data.message_id)
