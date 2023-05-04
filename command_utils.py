import copy

import pytz
import telebot

import config_utils
import utils


def initialize_bot_commands(bot: telebot.TeleBot):
	commands = []
	for command in COMMAND_LIST:
		command_text, description, _ = command
		commands.append(telebot.types.BotCommand(command_text, description))
	bot.set_my_commands(commands, telebot.types.BotCommandScopeAllPrivateChats())


def handle_command(bot: telebot.TeleBot, msg_data: telebot.types.Message):
	text = msg_data.text
	for command in COMMAND_LIST:
		command_text, _, handler = command
		if text.startswith(command_text):
			command_end_pos = text.find(" ")
			arguments = text[command_end_pos + 1:]
			return handler(bot, msg_data, arguments)


def handle_help_command(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	help_text = ""
	help_text += "/set_dump_chat_id <CHAT_ID> — changes dump chat id\n\n"
	help_text += "/set_interval_check_time <MINUTES> — changes delay between interval checks\n\n"
	help_text += "/add_main_channel <CHANNEL_ID> — add main channel\n\n"
	help_text += "/remove_main_channel <CHANNEL_ID> — remove main channel\n\n"
	help_text += "/enable_auto_forwarding — enables auto forwarding tickets found during scanning\n\n"
	help_text += "/disable_auto_forwarding — disables auto forwarding tickets found during scanning\n\n"

	help_text += "/set_timezone <TIMEZONE> — changes timezone identifier\n"
	help_text += "Example: /set_timezone Europe/Kiev\n\n"
	help_text += "/set_subchannel <MAIN_CHANNEL_ID> <TAG> <PRIORITY> <SUBCHANNEL_ID> — add subchannel to main channel with specified tag and priority\n"
	help_text += "Example: /set_subchannel -100987987987 aa 1 -100123321123\n\n"
	help_text += "/remove_subchannel_tag <MAIN_CHANNEL_ID> <TAG> — removes all subchannels with specified tag in main channel\n"
	help_text += "Example: /remove_subchannel_tag -100987987987 aa\n\n"
	help_text += "/set_user_tag <MAIN_CHANNEL_ID> <TAG> <USERNAME_OR_USER_ID> — add or change username or user id of the tag\n"
	help_text += "Example with username: /set_user_tag -100987987987 aa @username\n"
	help_text += "Example with user id: /set_user_tag -100987987987 aa 321123321\n\n"
	help_text += "/remove_user_tag <MAIN_CHANNEL_ID> <TAG> — remove user assigned to specified tag\n"
	help_text += "Example with username: /remove_user_tag -100987987987 aa\n\n"
	help_text += "/set_default_subchannel <MAIN_CHANNEL_ID> <DEFAULT_USER_TAG> <DEFAULT_PRIORITY> — changes default subchannel\n"
	help_text += "Example: /set_user_tag -100987987987 aa 1\n\n"
	help_text += "/set_storage_channel <MAIN_CHANNEL_ID> <STORAGE_CHANNEL_ID> — changes storage channel for scheduled messages\n"
	bot.send_message(chat_id=msg_data.chat.id, text=help_text)


def handle_set_dump_chat_id(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		dump_chat_id = int(arguments)
	except ValueError:
		bot.send_message(chat_id=msg_data.chat.id, text="You need to specify chat id.")
		return
	config_utils.DUMP_CHAT_ID = dump_chat_id
	bot.send_message(chat_id=msg_data.chat.id, text="Dump chat id successfully changed.")
	config_utils.update_config({"DUMP_CHAT_ID": config_utils.DUMP_CHAT_ID})


def handle_set_interval_check(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		interval = int(arguments)
	except ValueError:
		bot.send_message(chat_id=msg_data.chat.id, text="You need to specify number of seconds.")
		return
	config_utils.UPDATE_INTERVAL = interval
	bot.send_message(chat_id=msg_data.chat.id, text="Interval successfully changed.")
	config_utils.update_config({"UPDATE_INTERVAL": config_utils.UPDATE_INTERVAL})


def handle_set_timezone(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		pytz.timezone(arguments)
	except pytz.exceptions.UnknownTimeZoneError:
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong timezone identifier.")
		return
	config_utils.TIMEZONE_NAME = arguments
	bot.send_message(chat_id=msg_data.chat.id, text="Timezone successfully changed.")
	config_utils.update_config({"TIMEZONE_NAME": config_utils.TIMEZONE_NAME})


def handle_main_channel_change(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		channel_id = int(arguments)
	except ValueError:
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong channel id.")
		return

	if msg_data.text.startswith("/add_main_channel"):
		if channel_id in config_utils.CHANNEL_IDS:
			bot.send_message(chat_id=msg_data.chat.id, text="This channel already added.")
			return
		config_utils.CHANNEL_IDS.append(channel_id)
		bot.send_message(chat_id=msg_data.chat.id, text="Main channel was successfully added.")
	elif msg_data.text.startswith("/remove_main_channel"):
		if channel_id not in config_utils.CHANNEL_IDS:
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
			return
		config_utils.CHANNEL_IDS.remove(channel_id)
		bot.send_message(chat_id=msg_data.chat.id, text="Main channel was successfully removed.")

	config_utils.update_config({"CHANNEL_IDS": config_utils.CHANNEL_IDS})


def handle_subchannel_change(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	if msg_data.text.startswith("/set_subchannel"):
		try:
			main_channel_id, tag, priority, subchannel_id = arguments.split(" ")
			subchannel_id = int(subchannel_id)
		except ValueError:
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
			return

		if not utils.is_main_channel_exists(main_channel_id):
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
			return

		if main_channel_id not in config_utils.SUBCHANNEL_DATA:
			config_utils.SUBCHANNEL_DATA[main_channel_id] = {}
		if tag not in config_utils.SUBCHANNEL_DATA[main_channel_id]:
			config_utils.SUBCHANNEL_DATA[main_channel_id][tag] = {}

		config_utils.SUBCHANNEL_DATA[main_channel_id][tag][priority] = subchannel_id
		bot.send_message(chat_id=msg_data.chat.id, text="Subchannel data was successfully updated.")
	elif msg_data.text.startswith("/remove_subchannel_tag"):
		try:
			main_channel_id, tag = arguments.split(" ")
			main_channel_id = int(main_channel_id)
		except ValueError:
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
			return

		if not utils.is_main_channel_exists(main_channel_id):
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
			return

		if main_channel_id not in config_utils.SUBCHANNEL_DATA:
			bot.send_message(chat_id=msg_data.chat.id, text="Main channel not found in subchannel data.")
			return
		if tag not in config_utils.SUBCHANNEL_DATA[main_channel_id]:
			bot.send_message(chat_id=msg_data.chat.id, text="Tag not found in subchannel data.")
			return
		del config_utils.SUBCHANNEL_DATA[main_channel_id][tag]
		bot.send_message(chat_id=msg_data.chat.id, text="Subchannel data was successfully updated.")

	config_utils.update_config({"SUBCHANNEL_DATA": config_utils.SUBCHANNEL_DATA})


def handle_user_change(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	if msg_data.text.startswith("/set_user_tag"):
		try:
			main_channel_id, tag, user = arguments.split(" ")
		except ValueError:
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
			return

		if not utils.is_main_channel_exists(main_channel_id):
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
			return

		if main_channel_id not in config_utils.USER_DATA:
			config_utils.USER_DATA[main_channel_id] = {}

		config_utils.USER_DATA[main_channel_id][tag] = user
		bot.send_message(chat_id=msg_data.chat.id, text="User tag was successfully updated.")
	elif msg_data.text.startswith("/remove_user_tag"):
		try:
			main_channel_id, tag = arguments.split(" ")
		except ValueError:
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
			return

		if not utils.is_main_channel_exists(main_channel_id):
			bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
			return

		if main_channel_id not in config_utils.USER_DATA:
			bot.send_message(chat_id=msg_data.chat.id, text="Main channel not found in user data.")
			return
		if tag not in config_utils.USER_DATA[main_channel_id]:
			bot.send_message(chat_id=msg_data.chat.id, text="Tag not found in user data.")
			return
		del config_utils.USER_DATA[main_channel_id][tag]
		bot.send_message(chat_id=msg_data.chat.id, text="User tag was removed updated.")

	config_utils.load_users(bot)
	user_data = copy.deepcopy(config_utils.USER_DATA)
	for channel_id in user_data:
		for tag in user_data[channel_id]:
			if type(user_data[channel_id][tag]) == telebot.types.Chat:
				user_data[channel_id][tag] = user_data[channel_id][tag].id
	config_utils.update_config({"USER_DATA": user_data})


def handle_set_default_subchannel(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		main_channel_id, tag, priority = arguments.split(" ")
	except ValueError:
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
		return

	if not utils.is_main_channel_exists(main_channel_id):
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
		return

	config_utils.DEFAULT_USER_DATA[main_channel_id] = f"{tag} {priority}"

	bot.send_message(chat_id=msg_data.chat.id, text="Default subchannel successfully changed.")
	config_utils.update_config({"DEFAULT_USER_DATA": config_utils.DEFAULT_USER_DATA})


def handle_set_storage_channel(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	try:
		main_channel_id, storage_channel_id = arguments.split(" ")
		storage_channel_id = int(storage_channel_id)
	except ValueError:
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong arguments.")
		return

	if not utils.is_main_channel_exists(main_channel_id):
		bot.send_message(chat_id=msg_data.chat.id, text="Wrong main channel id.")
		return

	config_utils.SCHEDULED_STORAGE_CHAT_IDS[main_channel_id] = storage_channel_id
	bot.send_message(chat_id=msg_data.chat.id, text="Storage for scheduled messages was successfully changed.")
	config_utils.update_config({"SCHEDULED_STORAGE_CHAT_IDS": config_utils.SCHEDULED_STORAGE_CHAT_IDS})


def handle_change_auto_forwarding(bot: telebot.TeleBot, msg_data: telebot.types.Message, arguments: str):
	if msg_data.text.startswith("/enable"):
		config_utils.AUTO_FORWARDING_ENABLED = True
	elif msg_data.text.startswith("/disable"):
		config_utils.AUTO_FORWARDING_ENABLED = False
	state = "enabled" if config_utils.AUTO_FORWARDING_ENABLED else "disabled"
	bot.send_message(chat_id=msg_data.chat.id, text=f"Auto forwarding now is {state}.")
	config_utils.update_config({"AUTO_FORWARDING_ENABLED": config_utils.AUTO_FORWARDING_ENABLED})


COMMAND_LIST = [
	["/help", "Command explanations", handle_help_command],
	["/set_dump_chat_id", "Set dump chat id", handle_set_dump_chat_id],
	["/set_interval_check_time", "Set time between interval checks", handle_set_interval_check],
	["/set_timezone", "Set timezone", handle_set_timezone],
	["/add_main_channel", "Add main channel", handle_main_channel_change],
	["/remove_main_channel", "Remove main channel", handle_main_channel_change],
	["/set_subchannel", "Add subchannel", handle_subchannel_change],
	["/remove_subchannel_tag", "Remove subchannel", handle_subchannel_change],
	["/set_user_tag", "Add user id", handle_user_change],
	["/remove_user_tag", "Remove user id", handle_user_change],
	["/set_default_subchannel", "Set default subchannel", handle_set_default_subchannel],
	["/set_storage_channel", "Set storage channel", handle_set_storage_channel],
	["/enable_auto_forwarding", "Enables auto forwarding during scanning", handle_change_auto_forwarding],
	["/disable_auto_forwarding", "Enables auto forwarding during scanning", handle_change_auto_forwarding],
]

