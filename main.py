import logging
import telebot

import command_utils
import config_utils
import forwarding_utils
import interval_updating_utils
import post_link_utils
import db_utils
import scheduled_messages_utils
import utils

import messages_export_utils
from config_utils import BOT_TOKEN, APP_API_ID, APP_API_HASH, CHANNEL_IDS, CHAT_IDS_TO_IGNORE, DISCUSSION_CHAT_DATA,\
	SUPPORTED_CONTENT_TYPES, INTERVAL_UPDATE_START_DELAY

db_utils.initialize_db()
logging.basicConfig(format='%(asctime)s - {%(pathname)s:%(lineno)d} %(levelname)s: %(message)s', level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, num_threads=4)

config_utils.BOT_ID = bot.user.id
config_utils.load_discussion_chat_ids(bot)
config_utils.load_users(bot)
CHAT_IDS_TO_IGNORE += utils.get_ignored_chat_ids()

command_utils.initialize_bot_commands(bot)
scheduled_messages_utils.start_scheduled_thread(bot)

if APP_API_ID and APP_API_HASH:
	pyrogram_app = messages_export_utils.init_pyrogram(APP_API_ID, APP_API_HASH, BOT_TOKEN)
	messages_export_utils.export_comments_from_discussion_chats(pyrogram_app)

interval_updating_utils.start_interval_updating(bot, INTERVAL_UPDATE_START_DELAY)

main_channel_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS


@bot.channel_post_handler(func=main_channel_filter, content_types=SUPPORTED_CONTENT_TYPES)
def handle_post(post_data: telebot.types.Message):
	db_utils.insert_or_update_last_msg_id(post_data.message_id, post_data.chat.id)

	main_channel_id_str = str(post_data.chat.id)
	if DISCUSSION_CHAT_DATA[main_channel_id_str] is None:
		edited_post = post_link_utils.add_link_to_new_post(bot, post_data)
		forwarding_utils.forward_and_add_inline_keyboard(bot, edited_post, use_default_user=True, force_forward=True)


@bot.message_handler(func=lambda msg_data: msg_data.is_automatic_forward, content_types=SUPPORTED_CONTENT_TYPES)
def handle_automatically_forwarded_message(msg_data: telebot.types.Message):
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

	db_utils.insert_or_update_discussion_message(main_message_id, main_channel_id, discussion_message_id)

	msg_data.chat.id = main_channel_id
	msg_data.message_id = main_message_id
	edited_post = post_link_utils.add_link_to_new_post(bot, msg_data)
	forwarding_utils.forward_and_add_inline_keyboard(bot, edited_post, use_default_user=True, force_forward=True)


@bot.channel_post_handler(func=lambda post_data: post_data.chat.id in utils.get_all_subchannel_ids(),
					 content_types=SUPPORTED_CONTENT_TYPES)
def handle_subchannel_message(post_data: telebot.types.Message):
	if post_data.forward_from_chat is None:
		return

	if post_data.forward_from_chat.id not in CHANNEL_IDS:
		return

	main_channel_id = post_data.forward_from_chat.id
	message_id = post_data.forward_from_message_id
	forwarded_message_id = post_data.message_id
	subchannel_id = post_data.chat.id

	db_utils.insert_copied_message(message_id, main_channel_id, forwarded_message_id, subchannel_id)


@bot.message_handler(func=lambda msg_data: msg_data.chat.id in DISCUSSION_CHAT_DATA.values(),
					 content_types=SUPPORTED_CONTENT_TYPES)
def handle_discussion_message(msg_data: telebot.types.Message):
	discussion_message_id = msg_data.message_id
	discussion_chat_id = msg_data.chat.id

	if msg_data.reply_to_message:
		reply_to_message_id = msg_data.reply_to_message.message_id

		sender_id = msg_data.from_user.id
		db_utils.insert_comment_message(reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id)

		main_channel_id = utils.get_key_by_value(DISCUSSION_CHAT_DATA, discussion_chat_id)
		if main_channel_id is None:
			return

		main_channel_id = int(main_channel_id)
		top_discussion_message_id = db_utils.get_comment_top_parent(discussion_message_id, discussion_chat_id)
		if top_discussion_message_id == discussion_message_id:
			return
		main_message_id = db_utils.get_main_from_discussion_message(top_discussion_message_id, main_channel_id)
		if main_message_id:
			interval_updating_utils.update_older_message(bot, main_channel_id, main_message_id)

	db_utils.insert_or_update_last_msg_id(discussion_message_id, discussion_chat_id)


@bot.edited_channel_post_handler(func=main_channel_filter, content_types=SUPPORTED_CONTENT_TYPES)
def handle_edited_post(post_data: telebot.types.Message):
	post_link_utils.update_post_link(bot, post_data)


@bot.my_chat_member_handler()
def handle_changed_permissions(message: telebot.types.ChatMemberUpdated):
	has_permissions = message.new_chat_member.can_edit_messages and message.new_chat_member.can_post_messages
	if has_permissions:
		logging.info(f"Bot received permissions for channel {message.chat.id}")
	else:
		logging.info(f"Bot permissions for channel {message.chat.id} was removed")


@bot.callback_query_handler(func=lambda call: main_channel_filter(call.message))
def handle_main_channel_keyboard_callback(call: telebot.types.CallbackQuery):
	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call)
	elif call.data.startswith(post_link_utils.CALLBACK_PREFIX):
		post_link_utils.handle_callback(bot, call)
	elif call.data.startswith(scheduled_messages_utils.CALLBACK_PREFIX):
		scheduled_messages_utils.handle_callback(bot, call)


@bot.callback_query_handler(func=lambda call: call.message.chat.id in utils.get_all_subchannel_ids())
def handle_subchannel_keyboard_callback(call: telebot.types.CallbackQuery):
	main_message_data = db_utils.get_main_message_from_copied(call.message.message_id, call.message.chat.id)
	if main_message_data is None:
		logging.info(f"Button event in unknown message {[call.message.message_id, call.message.chat.id]}")
		return
	main_message_id, main_channel_id = main_message_data
	subchannel_message_id = call.message.message_id
	subchannel_id = call.message.chat.id
	call.message.message_id = main_message_id
	call.message.chat.id = main_channel_id

	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call, subchannel_id, subchannel_message_id)
	if call.data.startswith(scheduled_messages_utils.CALLBACK_PREFIX):
		scheduled_messages_utils.handle_callback(bot, call, subchannel_id, subchannel_message_id)


@bot.callback_query_handler(func=lambda call: call.message.chat.id in utils.get_all_scheduled_storage_ids())
def handle_scheduled_keyboard_callback(call: telebot.types.CallbackQuery):
	main_message_data = db_utils.get_main_from_scheduled_message(call.message.message_id, call.message.chat.id)
	if main_message_data is None:
		logging.info(f"Button event in unknown message {[call.message.message_id, call.message.chat.id]}")
		return
	main_message_id, main_channel_id = main_message_data
	scheduled_message_id = call.message.message_id
	scheduled_channel_id = call.message.chat.id

	call.message.message_id = main_message_id
	call.message.chat.id = main_channel_id

	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call, scheduled_channel_id, scheduled_message_id)
	if call.data.startswith(scheduled_messages_utils.CALLBACK_PREFIX):
		scheduled_messages_utils.handle_callback(bot, call, scheduled_channel_id, scheduled_message_id)



@bot.message_handler(func=lambda msg: msg.text.startswith("/"), chat_types=["private"])
def handle_bot_command(msg_data: telebot.types.Message):
	user_id = msg_data.from_user.id
	username = msg_data.from_user.username
	if username:
		username = f"@{username}"
	if user_id not in config_utils.ADMIN_USERS and username not in config_utils.ADMIN_USERS:
		return
	command_utils.handle_command(bot, msg_data)


bot.infinity_polling()
