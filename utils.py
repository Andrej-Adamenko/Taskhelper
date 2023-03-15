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

	if "CHANNEL_IDS" not in config_json:
		config_json["CHANNEL_IDS"] = []

	config_data_list = []
	config_data_list.append(config_json["BOT_TOKEN"])
	config_data_list.append(config_json["CHANNEL_IDS"])

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



def get_post_url(post_data):
	channel_url = str(post_data.chat.id)[4:]
	return "https://t.me/c/{0}/{1}".format(channel_url, post_data.message_id)

def offset_entities(entities, offset):
	if not entities:
		return []

	for entity in entities:
		entity.offset += offset

	return entities

def get_previous_link(post_data, post_url):
	if post_data.entities:
		for entity in post_data.entities:
			if entity.offset == 0 and entity.type == "text_link" and entity.url == post_url:
				return entity
	return None
