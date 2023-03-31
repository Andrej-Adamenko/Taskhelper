from telebot.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton

import utils
import interval_updating_utils

LINK_ENDING = ". "

CALLBACK_PREFIX = "LNK"

START_UPDATE_QUESTION = "Do you want to start updating older posts? (This can take some time, bot can respond with delay until updating is complete)"


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
	if utils.get_forwarded_from_id(post_data) or post_data.text is None:
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
		if len(link_text) == previous_link.length and post_data.text.startswith(link_text + LINK_ENDING):
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


def update_older_messages_question(bot, chat_id):
	buttons = [
		InlineKeyboardButton("Yes", callback_data=utils.create_callback_str(CALLBACK_PREFIX, "UPD_YES")),
		InlineKeyboardButton("No", callback_data=utils.create_callback_str(CALLBACK_PREFIX, "UPD_NO"))
	]
	keyboard_markup = InlineKeyboardMarkup([buttons])

	bot.send_message(chat_id=chat_id, text=START_UPDATE_QUESTION, reply_markup=keyboard_markup)


def handle_callback(bot, call):
	callback_data = call.data[len(CALLBACK_PREFIX) + 1:]
	main_channel_id = call.message.chat.id

	if callback_data == "UPD_YES":
		interval_updating_utils.start_updating_older_messages(bot, main_channel_id, call.message.id)
	elif callback_data == "UPD_NO":
		bot.delete_message(chat_id=main_channel_id, message_id=call.message.id)

