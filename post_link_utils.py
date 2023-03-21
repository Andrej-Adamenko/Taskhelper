import logging
import time

from telebot.apihelper import ApiTelegramException
from telebot.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton

import utils
import forwarding_utils

LINK_ENDING = ". "

CALLBACK_PREFIX = "LNK"


def get_post_url(post_data):
	channel_url = str(post_data.chat.id)[4:]
	return "https://t.me/c/{0}/{1}".format(channel_url, post_data.message_id)


def get_previous_link(post_data, post_url):
	if post_data.entities:
		for entity in post_data.entities:
			if entity.offset == 0 and entity.type == "text_link" and entity.url == post_url:
				return entity
	return None


def insert_link_into_post(bot, post_data, link_text, post_url, additional_offset=0):
	updated_entities = utils.offset_entities(post_data.entities, len(link_text) + len(LINK_ENDING) + additional_offset)
	updated_entities.append(MessageEntity(type="text_link", offset=0, length=len(link_text), url=post_url))
	updated_entities.sort(key=lambda e: e.offset)

	post_data.text = link_text + LINK_ENDING + post_data.text
	post_data.entities = updated_entities
	bot.edit_message_text(text=post_data.text, chat_id=post_data.chat.id, message_id=post_data.message_id,
								 entities=post_data.entities, reply_markup=post_data.reply_markup)
	return post_data


def add_link_to_new_post(bot, post_data):
	# skip forwarded messages and messages without text
	if get_forwarded_from_id(post_data) or post_data.text is None:
		return

	post_url = get_post_url(post_data)
	link_text = str(post_data.message_id)

	return insert_link_into_post(bot, post_data, link_text, post_url)


def update_post_link(bot, post_data):
	if post_data.text is None:
		return

	post_url = get_post_url(post_data)
	link_text = str(post_data.message_id)

	entity_offset = 0

	previous_link = get_previous_link(post_data, post_url)
	if previous_link:
		if post_data.text.startswith(link_text + LINK_ENDING):
			return  # return if link is correct
		entity_offset = remove_previous_link(post_data, previous_link)

	return insert_link_into_post(bot, post_data, link_text, post_url, entity_offset)


def remove_previous_link(post_data, previous_link):
	entity_offset = 0

	post_data.text = post_data.text[previous_link.length:]
	entity_offset -= previous_link.length
	if post_data.text.startswith(LINK_ENDING):
		post_data.text = post_data.text[len(LINK_ENDING):]
		entity_offset -= len(LINK_ENDING)

	post_data.entities.remove(previous_link)

	return entity_offset


def start_updating_older_messages(bot, channel_id, dump_chat_id, subchannel_data):
	last_message = bot.send_message(chat_id=channel_id,
									text="Started updating older posts. When update is complete this message will be deleted.")
	current_msg_id = last_message.id - 1
	while current_msg_id > 0:
		time.sleep(3)
		try:
			update_older_message(bot, channel_id, current_msg_id, dump_chat_id, subchannel_data)
		except ApiTelegramException as E:
			if E.error_code == 429:
				logging.warning("Too many requests - " + str(E))
				time.sleep(20)
				continue
			logging.error("Error during updating older messages - " + str(E))

		current_msg_id -= 1

	bot.delete_message(chat_id=last_message.chat.id, message_id=last_message.id)


def update_older_message(bot, channel_id, current_msg_id, dump_chat_id, subchannel_data):
	try:
		forwarded_message = bot.forward_message(chat_id=dump_chat_id, from_chat_id=channel_id,
												message_id=current_msg_id)
		bot.delete_message(chat_id=dump_chat_id, message_id=forwarded_message.message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		return

	if get_forwarded_from_id(forwarded_message) != channel_id or forwarded_message.text is None:
		return

	forwarded_message.message_id = forwarded_message.forward_from_message_id
	forwarded_message.chat = forwarded_message.forward_from_chat

	updated_message = update_post_link(bot, forwarded_message)

	if not updated_message:
		updated_message = forwarded_message

	forwarding_utils.forward_and_add_inline_keyboard(bot, updated_message, subchannel_data)


def get_forwarded_from_id(message_data):
	if message_data.forward_from_chat:
		return message_data.forward_from_chat.id
	if message_data.forward_from:
		return message_data.forward_from.id

	return None


def update_older_messages_question(bot, chat_id):
	buttons = [
		InlineKeyboardButton("Yes", callback_data=utils.create_callback_str(CALLBACK_PREFIX, "UPD_YES")),
		InlineKeyboardButton("No", callback_data=utils.create_callback_str(CALLBACK_PREFIX, "UPD_NO"))
	]
	keyboard_markup = InlineKeyboardMarkup([buttons])

	question = "Do you want to start adding links to older posts? (This can take some time, bot will not respond until updating is complete)"
	bot.send_message(chat_id=chat_id, text=question, reply_markup=keyboard_markup)


def handle_callback(bot, call, dump_chat_id, subchannel_data):
	callback_data = call.data[len(CALLBACK_PREFIX) + 1:]
	chat_id = call.message.chat.id

	if callback_data == "UPD_YES":
		bot.delete_message(chat_id=chat_id, message_id=call.message.id)
		start_updating_older_messages(bot, chat_id, dump_chat_id, subchannel_data)
	elif callback_data == "UPD_NO":
		bot.delete_message(chat_id=chat_id, message_id=call.message.id)

