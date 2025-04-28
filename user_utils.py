import logging
from typing import Union

import telebot.types
from telebot.apihelper import ApiTelegramException

import config_utils
import core_api
import db_utils
import threading_utils

USER_DATA: dict = {}


def get_signature(user: Union[telebot.types.User, telebot.types.Chat]):
	if user.first_name and user.last_name:
		return user.first_name + " " + user.last_name

	return user.first_name if user.first_name else user.last_name


def find_user_by_signature(signature: str):
	for user_tag in USER_DATA:
		user = USER_DATA[user_tag]
		if type(user) == telebot.types.User:
			current_signature = get_signature(user)
			if current_signature == signature:
				return user.id


def load_users(bot: telebot.TeleBot):
	global USER_DATA

	USER_DATA = config_utils.USER_TAGS.copy()

	for user_tag in USER_DATA:
		user_id = USER_DATA.get(user_tag)
		user_info = get_user(bot, user_id)
		if not user_info:
			continue
		USER_DATA[user_tag] = user_info


@threading_utils.timeout_error_lock
def get_user(bot: telebot.TeleBot, user: Union[str, int]):
	try:
		user_chat = bot.get_chat(user)
		return telebot.types.User(
			id=user_chat.id,
			first_name=user_chat.first_name,
			last_name=user_chat.last_name,
			username=user_chat.username,
			is_bot=False
		)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.error(f"Error during loading info about user {user} using bot api: {E}")

	# try to get user using core api because in some cases bot api can't find the user by id
	core_api_user = core_api.get_user(user)
	if core_api_user:
		return telebot.types.User(
			id=core_api_user.id,
			first_name=core_api_user.first_name,
			last_name=core_api_user.last_name,
			username=core_api_user.username,
			is_bot=False
		)

	logging.error(f"Error during loading info about user {user} using core api")


def insert_user_reference(user_tag: str, text: str):
	placeholder_text = "{USER}"
	placeholder_position = text.find(placeholder_text)
	if placeholder_position < 0:
		return text, None

	text = text[:placeholder_position] + text[placeholder_position + len(placeholder_text):]

	if user_tag not in USER_DATA:
		text = text[:placeholder_position] + user_tag + text[placeholder_position:]
		return text, None

	user = USER_DATA[user_tag]
	if type(user) == telebot.types.User:
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
