from typing import List

import telebot.types


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


def get_post_content(post_data: telebot.types.Message):
	if post_data.text is not None:
		return post_data.text, post_data.entities
	elif post_data.caption is not None:
		return post_data.caption, post_data.caption_entities

	return "", []


def set_post_content(post_data: telebot.types.Message, text: str, entities: telebot.types.MessageEntity):
	if post_data.text is not None:
		post_data.text = text
		post_data.entities = entities
	else:
		post_data.caption = text
		post_data.caption_entities = entities


def edit_message_content(bot: telebot.TeleBot, post_data: telebot.types.Message, **kwargs):
	if post_data.text is not None:
		bot.edit_message_text(chat_id=post_data.chat.id, message_id=post_data.message_id, **kwargs)
	else:
		kwargs["caption"] = kwargs.pop("text")
		kwargs["caption_entities"] = kwargs.pop("entities")
		bot.edit_message_caption(chat_id=post_data.chat.id, message_id=post_data.message_id, **kwargs)

