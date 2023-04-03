import logging
import telebot

import forwarding_utils
import interval_updating_utils
import post_link_utils
import config_utils
import db_utils

from config_utils import BOT_TOKEN, CHANNEL_IDS, DUMP_CHAT_ID, DISCUSSION_CHAT_DATA

db_utils.initialize_db()

CHAT_IDS_TO_IGNORE = forwarding_utils.get_all_subchannel_ids()
CHAT_IDS_TO_IGNORE.append(DUMP_CHAT_ID)
CHAT_IDS_TO_IGNORE += forwarding_utils.get_all_discussion_chat_ids()

logging.basicConfig(format='%(asctime)s - {%(pathname)s:%(lineno)d} %(levelname)s: %(message)s', level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, num_threads=4)

config_utils.load_discussion_chat_ids(bot)

interval_updating_utils.start_interval_updating(bot)

channel_id_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS


@bot.channel_post_handler(func=channel_id_filter,
						  content_types=['audio', 'photo', 'voice', 'video', 'document', 'text'])
def handle_post(post_data):
	db_utils.insert_or_update_last_msg_id(post_data.message_id, post_data.chat.id)

	edited_post = post_link_utils.add_link_to_new_post(bot, post_data)
	main_channel_id_str = str(post_data.chat.id)
	if main_channel_id_str not in DISCUSSION_CHAT_DATA:
		forwarding_utils.forward_and_add_inline_keyboard(bot, edited_post, True)


@bot.message_handler(func=lambda msg_data: msg_data.is_automatic_forward)
def handle_automatically_forwarded_message(msg_data):
	db_utils.insert_or_update_last_msg_id(msg_data.message_id, msg_data.chat.id)

	if msg_data.text == interval_updating_utils.UPDATE_STARTED_MSG_TEXT or msg_data.text == post_link_utils.START_UPDATE_QUESTION:
		return

	forwarded_from_str = str(msg_data.forward_from_chat.id)
	if forwarded_from_str not in DISCUSSION_CHAT_DATA:
		return

	discussion_chat_id = DISCUSSION_CHAT_DATA[forwarded_from_str]
	if discussion_chat_id != msg_data.chat.id:
		return

	main_channel_id = msg_data.forward_from_chat.id
	main_message_id = msg_data.forward_from_message_id
	discussion_message_id = msg_data.message_id

	db_utils.insert_discussion_message(main_message_id, main_channel_id, discussion_message_id)

	msg_data.chat.id = main_channel_id
	msg_data.message_id = main_message_id
	forwarding_utils.forward_and_add_inline_keyboard(bot, msg_data, True)


@bot.edited_channel_post_handler(func=channel_id_filter)
def handle_edited_post(post_data):
	post_link_utils.update_post_link(bot, post_data)


@bot.my_chat_member_handler()
def handle_changed_permissions(message):
	chat_id = message.chat.id
	if chat_id in CHAT_IDS_TO_IGNORE:
		return

	has_permissions = message.new_chat_member.can_edit_messages and message.new_chat_member.can_post_messages

	if has_permissions and chat_id in CHANNEL_IDS:
		return  # channel_id already added to config file

	if not has_permissions and chat_id not in CHANNEL_IDS:
		return  # channel_id already remove from config file

	if has_permissions:
		CHANNEL_IDS.append(chat_id)
		post_link_utils.update_older_messages_question(bot, chat_id)
		logging.info(f"Channel {chat_id} was added to config")
	else:
		CHANNEL_IDS.remove(chat_id)
		logging.info(f"Channel {chat_id} was removed from config")

	config_utils.update_config({"CHANNEL_IDS": CHANNEL_IDS})


@bot.callback_query_handler(func=lambda call: channel_id_filter(call.message))
def handle_keyboard_callback(call: telebot.types.CallbackQuery):
	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call)
	elif call.data.startswith(post_link_utils.CALLBACK_PREFIX):
		post_link_utils.handle_callback(bot, call)


bot.infinity_polling()
