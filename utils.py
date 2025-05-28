import logging
from typing import List
import time
import datetime

import pyrogram.types
import telebot.types
from telebot.apihelper import ApiTelegramException
from telebot.types import MessageEntity

import config_utils
import db_utils
import post_link_utils
import threading_utils
import channel_manager
from config_utils import MAX_BUTTONS_IN_ROW

SAME_MSG_CONTENT_ERROR = "Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
MSG_CANT_BE_DELETED_ERROR = "message can't be deleted"
MSG_NOT_FOUND_ERROR = "message to delete not found"
KICKED_FROM_CHANNEL_ERROR = "Forbidden: bot was kicked from the channel chat"


def align_entities_to_utf8(text: str, entities: List[telebot.types.MessageEntity]):
	if not entities:
		return []

	aligned_entities = []
	remained_entities = [e for e in entities if not getattr(e, "aligned_to_utf8", False)]
	for i, c in enumerate(text):
		if ord(c) > 0xffff:
			remained_entities = [e for e in remained_entities if e.offset > i]
			for entity in remained_entities:
				entity.offset -= 1
				if entity not in aligned_entities:
					aligned_entities.append(entity)

	for entity in aligned_entities:
		entity.aligned_to_utf8 = True

	return entities


def align_entities_to_utf16(text: str, entities: List[telebot.types.MessageEntity]):
	if not entities:
		return []

	aligned_entities = []
	remained_entities = [e for e in entities if getattr(e, "aligned_to_utf8", False)]
	for i, c in enumerate(text):
		if ord(c) > 0xffff:
			remained_entities = [e for e in remained_entities if e.offset > i]
			for entity in remained_entities:
				entity.offset += 1
				if entity not in aligned_entities:
					aligned_entities.append(entity)

	for entity in aligned_entities:
		entity.aligned_to_utf8 = False

	return entities


def create_callback_str(callback_prefix, callback_type, *args):
	arguments_str = ",".join([str(arg) for arg in args])
	components = [callback_prefix, callback_type]
	if arguments_str:
		components.append(arguments_str)
	callback_str = ",".join(components)
	return callback_str


def parse_callback_str(callback_str: str):
	callback_type = ""
	arguments = []
	if callback_str is not None and callback_str != config_utils.EMPTY_CALLBACK_DATA_BUTTON:
		components = callback_str.split(",")
		callback_type = components[1]
		arguments = components[2:]

	return callback_type, arguments


def offset_entities(entities, offset, expect_offsets: list=None):
	if not entities:
		return []

	for entity in entities:
		if not expect_offsets or entity.offset not in expect_offsets:
			entity.offset += offset

	return entities


def get_forwarded_from_id(message_data):
	if message_data.forward_from_chat:
		return message_data.forward_from_chat.id
	if message_data.forward_from:
		return message_data.forward_from.id

	return None


def replace_whitespaces(text):
	result = ""
	for c in text:
		result += " " if (c not in ['\n', '\t'] and c.isspace()) else c
	return result


def get_post_content(post_data: telebot.types.Message):
	text = ""
	entities = []
	if post_data.text is not None:
		entities = align_entities_to_utf8(post_data.text, post_data.entities)
		text = post_data.text
	elif post_data.caption is not None:
		entities = align_entities_to_utf8(post_data.caption, post_data.caption_entities)
		text = post_data.caption

	return replace_whitespaces(text), entities


def set_post_content(post_data: telebot.types.Message, text: str, entities: List[telebot.types.MessageEntity]):
	if post_data.text is not None:
		post_data.text = text
		post_data.entities = entities
	else:
		post_data.caption = text
		post_data.caption_entities = entities


@threading_utils.timeout_error_lock
def edit_message_content(bot: telebot.TeleBot, post_data: telebot.types.Message, **kwargs):
	if "chat_id" not in kwargs:
		kwargs["chat_id"] = post_data.chat.id
	if "message_id" not in kwargs:
		kwargs["message_id"] = post_data.message_id
	if "text" not in kwargs:
		kwargs["text"] = post_data.text if post_data.text else post_data.caption
	if "entities" not in kwargs:
		kwargs["entities"] = post_data.entities if post_data.entities else post_data.caption_entities

	kwargs["entities"] = align_entities_to_utf16(kwargs["text"], kwargs["entities"])

	try:
		if post_data.text is not None:
			bot.edit_message_text(**kwargs)
		else:
			kwargs["caption"] = kwargs.pop("text")
			kwargs["caption_entities"] = kwargs.pop("entities")
			bot.edit_message_caption(**kwargs)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return


def is_post_data_equal(post_data: telebot.types.Message, post_data_original: telebot.types.Message):
	text1, entities1 = get_post_content(post_data)
	text2, entities2 = get_post_content(post_data_original)

	entities1 = [e for e in entities1 if e.type != "phone_number"]
	entities2 = [e for e in entities2 if e.type != "phone_number"]

	if text1 != text2:
		return False

	if entities1 is None and entities2 is None:
		return True

	if len(entities1) != len(entities2):
		return False

	for entity_i in range(len(entities1)):
		e1 = entities1[entity_i]
		e2 = entities2[entity_i]
		if e1.type != e2.type or e1.offset != e2.offset or e1.url != e2.url:
			return False

		if e1.type == "hashtag":
			return True  # for hashtags length is ignored because length of deferred tags can be changed
		else:
			return e1.length == e2.length

	return True


def add_channel_id_to_post_data(post_data: telebot.types.Message):
	channel_id = post_data.chat.id

	channel_ids = db_utils.get_main_channel_ids()
	if len(channel_ids) > 1 and channel_id in channel_ids:
		channel_name = post_data.chat.title
		text, entities = get_post_content(post_data)
		if entities[0].type == 'text_link' and entities[0].offset == 0 and entities[0].length == len(str(post_data.id)):
			offset_entities(entities, len(str(channel_name)) + 1, [0])
			text = f"{channel_name}.{text}"
			entities[0].length += len(str(channel_name)) + 1

		set_post_content(post_data, text, entities)


def place_buttons_in_rows(buttons: List[telebot.types.InlineKeyboardButton]):
	rows = [[]]
	current_row = button_counter = 0
	for button in buttons:
		if button_counter < MAX_BUTTONS_IN_ROW:
			rows[current_row].append(button)
			button_counter += 1
		else:
			button_counter = 1
			current_row += 1
			rows.append([button])

	return rows


@threading_utils.timeout_error_lock
def edit_message_keyboard(bot: telebot.TeleBot, post_data: telebot.types.Message,
                          keyboard_markup: telebot.types.InlineKeyboardMarkup = None, chat_id: int = None, message_id: int = None):
	if chat_id is None and message_id is None:
		chat_id = post_data.chat.id
		message_id = post_data.message_id

	if keyboard_markup is None:
		keyboard_markup = post_data.reply_markup

	if db_utils.is_individual_channel_exists(chat_id):
		newest_message_id = db_utils.get_newest_copied_message(chat_id)
		if message_id == newest_message_id:

			# copy keyboard markup object to prevent modification of an original object
			keyboard_markup = merge_keyboard_markup(keyboard_markup,
								channel_manager.get_ticket_settings_buttons(chat_id))

	try:
		bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard_markup)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		if E.description == SAME_MSG_CONTENT_ERROR:
			return
		logging.info(f"Exception during adding keyboard - {E}")


def cut_entity_from_post(text: str, entities: List[telebot.types.MessageEntity], entity_index: int):
	entity_to_cut = entities[entity_index]
	if len(text) > entity_to_cut.offset + entity_to_cut.length:
		character_after_entity = text[entity_to_cut.offset + entity_to_cut.length]
		if character_after_entity == " ":
			entity_to_cut.length += 1
	elif text[entity_to_cut.offset - 1] == " ":
		# remove space before last tag if it's at the end of the line
		entity_to_cut.offset -= 1
		entity_to_cut.length += 1

	end = text[entity_to_cut.offset + entity_to_cut.length:]
	text = text[:entity_to_cut.offset] + end
	offsetted_entities = offset_entities(entities[entity_index + 1:], -entity_to_cut.length)
	entities[entity_index:] = offsetted_entities

	return text, entities


def get_key_by_value(d: dict, value: object):
	key_list = list(d.keys())
	val_list = list(d.values())

	try:
		position = val_list.index(value)
	except ValueError:
		return

	return key_list[position]


def get_keys_by_value(d: dict, search: object):
	result = []
	for key, value in d.items():
		if value == search:
			result.append(key)

	return result


@threading_utils.timeout_error_lock
def delete_message(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		return bot.delete_message(chat_id=chat_id, message_id=message_id)
	except ApiTelegramException as E:
		if E.description.endswith(MSG_NOT_FOUND_ERROR):
			return True
		else:
			raise E


def get_last_message(bot: telebot.TeleBot, channel_id: int):
	last_message_id = db_utils.get_last_message_id(channel_id)
	if last_message_id is None:
		msg_text = "(This is service message for obtaining last message id, bot will delete it in a moment)"
		try:
			last_message = bot.send_message(chat_id=channel_id, text=msg_text)
			bot.delete_message(chat_id=channel_id, message_id=last_message.message_id)
		except Exception as E:
			logging.error(f"Error during retrieving last message id in {channel_id} - {E}")
			return
		last_message_id = last_message.message_id - 1
		db_utils.insert_or_update_last_msg_id(last_message_id, channel_id)

	return last_message_id


def check_last_messages(bot: telebot.TeleBot):
	channels_to_check = set()

	main_channel_ids = db_utils.get_main_channel_ids()
	if main_channel_ids:
		channels_to_check.update(main_channel_ids)

	for main_channel_id in config_utils.DISCUSSION_CHAT_DATA:
		discussion_channel_id = config_utils.DISCUSSION_CHAT_DATA[main_channel_id]
		if discussion_channel_id:
			channels_to_check.add(discussion_channel_id)

	for channel_id in channels_to_check:
		get_last_message(bot, channel_id)


@threading_utils.timeout_error_lock
def add_comment_to_ticket(bot: telebot.TeleBot, post_data: telebot.types.Message, text: str, entities: list = None):
	main_message_id = post_data.message_id
	main_channel_id = post_data.chat.id
	comment_message_id = db_utils.get_discussion_message_id(main_message_id, main_channel_id)
	if comment_message_id:
		main_channel_id_str = str(main_channel_id)
		discussion_chat_id = config_utils.DISCUSSION_CHAT_DATA[main_channel_id_str]
		if discussion_chat_id is None:
			return
		comment_msg = bot.send_message(chat_id=discussion_chat_id, reply_to_message_id=comment_message_id, text=text, entities=entities)
		db_utils.insert_comment_message(comment_message_id, comment_msg.id, discussion_chat_id, config_utils.BOT_ID)
		db_utils.set_ticket_update_time(main_message_id, main_channel_id, int(time.time()))


@threading_utils.timeout_error_lock
def get_message_content_by_id(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		forwarded_message = bot.forward_message(chat_id=config_utils.DUMP_CHAT_ID, from_chat_id=chat_id,
												message_id=message_id)
		bot.delete_message(chat_id=config_utils.DUMP_CHAT_ID, message_id=forwarded_message.message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.error(f"Error during getting message {[message_id, chat_id]} content - {E}")
		return

	_update_forwarded_message_chat(forwarded_message, chat_id, message_id)
	return forwarded_message


@threading_utils.timeout_error_lock
def get_main_message_content_by_id(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		forwarded_message = bot.forward_message(chat_id=config_utils.DUMP_CHAT_ID, from_chat_id=chat_id,
												message_id=message_id)
		bot.delete_message(chat_id=config_utils.DUMP_CHAT_ID, message_id=forwarded_message.message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		elif E.description == "Bad Request: message to forward not found":
			raise E
		elif E.description == "Bad Request: MESSAGE_ID_INVALID":
			# for some reason telegram throws this error if after deleting a message
			# no other actions were performed in this channel
			# instead of regular "message to forward not found" error
			raise E
		logging.error(f"Error during getting message content - {E}")
		return

	_update_forwarded_message_chat(forwarded_message, chat_id, message_id)
	return forwarded_message


def _update_forwarded_message_chat(post_data: telebot.types.Message, chat_id: int, message_id: int):
	if post_data.forward_from_chat and post_data.forward_from_chat.id == chat_id:
		post_data.chat = post_data.forward_from_chat
	else:
		post_data.chat.id = chat_id

	post_data.message_id = post_data.id = post_data.forward_from_message_id

@threading_utils.timeout_error_lock
def copy_message(bot: telebot.TeleBot, **kwargs):
	return bot.copy_message(**kwargs)


@threading_utils.timeout_error_lock
def remove_keyboard(bot: telebot.TeleBot, chat_id: int, message_id: int):
	bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)


def check_content_type(bot: telebot.TeleBot, message: telebot.types.Message):
	if message.content_type not in config_utils.SUPPORTED_CONTENT_TYPES_TICKET:
		if message.reply_markup:
			chat_id = message.chat.id
			message_id = message.message_id
			remove_keyboard(bot, chat_id, message_id)
		return False
	return True


def parse_datetime(datetime_str, template_str):
	try:
		return datetime.datetime.strptime(datetime_str, template_str)
	except ValueError:
		return


@threading_utils.timeout_error_lock
def mark_message_for_deletion(bot: telebot.TeleBot, chat_id: int, message_id: int):
	try:
		bot.edit_message_text(text=config_utils.TO_DELETE_MSG_TEXT, chat_id=chat_id, message_id=message_id)
	except ApiTelegramException as E:
		if E.error_code == 429:
			raise E
		logging.info(f"Error during marking message{chat_id, message_id} for deletion {E}")

def merge_keyboard_markup(
		keyboard: telebot.types.InlineKeyboardMarkup,
		*keyboard2: telebot.types.InlineKeyboardMarkup,
		empty_button = telebot.types.InlineKeyboardButton(" ", callback_data=config_utils.EMPTY_CALLBACK_DATA_BUTTON)):

	result = keyboard.keyboard.copy()

	for board in keyboard2:
		if len(board.keyboard) > 0 and len(result) > 0 and empty_button:
			result += [[empty_button]]

		result += board.keyboard

	return telebot.types.InlineKeyboardMarkup(result)

def update_forwarded_fields(message: pyrogram.types.Message) -> None:
	message.entities = __update_entities(message.entities) if message.entities else None
	message.caption_entities = __update_entities(message.caption_entities) if message.caption_entities else None
	message.content_type = __get_content_type_pyrogram_message(message)
	message.message_id = message.id

def __update_entities(entities: list) -> list:
	result = []
	for ent in entities:
		result.append(MessageEntity(type=ent.type.name.lower(), offset=ent.offset, length=ent.length,
									url=ent.url if hasattr(ent, "url") and ent.url is not None else None,
									custom_emoji_id=ent.custom_emoji_id if hasattr(ent, "custom_emoji_id") and ent.custom_emoji_id is not None else None,
									language=ent.language if hasattr(ent, "language") and ent.language is not None else None,
									user=ent.user if hasattr(ent, "user") and ent.user is not None else None))
	return result

def __get_content_type_pyrogram_message(message: pyrogram.types.Message):
	# order is important: for example, a photo may contain a caption, so we check photo before text
	attrs = [
		"photo", "video", "audio", "document", "sticker", "video_note",
		"voice", "location", "contact", "venue", "dice", "poll", "text"
	]
	for attr in attrs:
		if getattr(message, attr) is not None:
			return attr
	return "unknown"