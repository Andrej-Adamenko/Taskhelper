import logging
from typing import Union

import telebot.types

import config_utils
import db_utils

USER_DATA = {}


def get_signature(user: Union[telebot.types.User, telebot.types.Chat]):
	if user.first_name and user.last_name:
		return user.first_name + " " + user.last_name

	return user.first_name if user.first_name else user.last_name


def find_user_by_signature(signature: str, main_channel_id: int):
	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in USER_DATA:
		return
	for user_tag in USER_DATA[main_channel_id_str]:
		user = USER_DATA[main_channel_id_str][user_tag]
		if type(user) == telebot.types.Chat:
			current_signature = get_signature(user)
			if current_signature == signature:
				return user.id


def load_users(bot: telebot.TeleBot):
	user_data = db_utils.get_all_users()
	for user in user_data:
		main_channel_id, user_id, user_tag = user
		main_channel_id = str(main_channel_id)
		if main_channel_id not in USER_DATA:
			USER_DATA[str(main_channel_id)] = {}

		USER_DATA[main_channel_id][user_tag] = user_id
		try:
			user_info = bot.get_chat(user_id)
		except Exception as E:
			logging.error(f"Error during loading info about user {user_id}, {E}")
			continue
		USER_DATA[main_channel_id][user_tag] = user_info


def insert_user_reference(main_channel_id: int, user_tag: str, text: str):
	placeholder_text = "{USER}"
	placeholder_position = text.find(placeholder_text)
	if placeholder_position < 0:
		return text, None

	text = text[:placeholder_position] + text[placeholder_position + len(placeholder_text):]

	main_channel_id_str = str(main_channel_id)
	if main_channel_id_str not in USER_DATA:
		text = text[:placeholder_position] + user_tag + text[placeholder_position:]
		return text, None
	user_tags = USER_DATA[main_channel_id_str]
	if user_tag not in user_tags:
		text = text[:placeholder_position] + user_tag + text[placeholder_position:]
		return text, None

	user = user_tags[user_tag]
	if type(user) == telebot.types.Chat:
		if user.username:
			user_reference_text = f"@{user.username}"
			text = text[:placeholder_position] + user_reference_text + text[placeholder_position:]
			return text, None
		else:
			user_reference_text = user.first_name
			text = text[:placeholder_position] + user_reference_text + text[placeholder_position:]
			mentioned_user = {"id": user.id, "first_name": user.first_name, "last_name": user.last_name}
			entity = telebot.types.MessageEntity(offset=placeholder_position, length=len(user_reference_text),
			                                     type="text_mention", user=mentioned_user)
			return text, [entity]
	else:
		text = text[:placeholder_position] + str(user) + text[placeholder_position:]
		return text, None
