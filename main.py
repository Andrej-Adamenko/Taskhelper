import datetime
import logging
import time

import telebot
from telebot.types import ChatMemberOwner
from telebot.apihelper import ApiTelegramException

import channel_manager
import command_utils
from comment_utils import comment_dispatcher
import config_utils
import daily_reminder
import forwarding_utils
import interval_updating_utils
import post_link_utils
import db_utils
from scheduled_messages_utils import scheduled_message_dispatcher
import user_utils
import utils

import messages_export_utils
from config_utils import (BOT_TOKEN, DISCUSSION_CHAT_DATA, SUPPORTED_CONTENT_TYPES_TICKET,
						  SUPPORTED_CONTENT_TYPES_COMMENT, INTERVAL_UPDATE_START_DELAY)

db_utils.initialize_db()
logging.basicConfig(format='%(asctime)s - {%(pathname)s:%(lineno)d} %(levelname)s: %(message)s', level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN, num_threads=1)

config_utils.BOT_ID = bot.user.id
config_utils.load_discussion_chat_ids(bot)
config_utils.add_users_from_db()
user_utils.load_users(bot)

utils.check_last_messages(bot)

command_utils.initialize_bot_commands(bot)
scheduled_message_dispatcher.start_scheduled_thread(bot)

daily_reminder.start_reminder_thread(bot)

messages_export_utils.start_exporting()
user_utils.update_all_channel_members()
user_utils.check_members_on_main_channels(bot)
forwarding_utils.get_invalid_ticket_ids(bot)

interval_updating_utils.start_interval_updating(bot, INTERVAL_UPDATE_START_DELAY)

main_channel_filter = lambda message_data: db_utils.is_main_channel_exists(message_data.chat.id)
subchannel_filter = lambda message_data: db_utils.is_individual_channel_exists(message_data.chat.id)


@bot.channel_post_handler(func=main_channel_filter, content_types=SUPPORTED_CONTENT_TYPES_TICKET)
def handle_post(post_data: telebot.types.Message):
	db_utils.insert_or_update_last_msg_id(post_data.message_id, post_data.chat.id)
	if post_data.media_group_id:
		return

	user_id = user_utils.find_user_by_signature(post_data.author_signature)
	db_utils.insert_main_channel_message(post_data.chat.id, post_data.message_id, user_id)

	main_channel_id_str = str(post_data.chat.id)
	if DISCUSSION_CHAT_DATA[main_channel_id_str] is None:
		edited_post = post_link_utils.add_link_to_new_post(post_data)
		forwarding_utils.forward_and_add_inline_keyboard(bot, edited_post, new_ticket=True)


@bot.message_handler(func=lambda msg_data: msg_data.is_automatic_forward, content_types=SUPPORTED_CONTENT_TYPES_TICKET)
def handle_automatically_forwarded_message(msg_data: telebot.types.Message):
	db_utils.insert_or_update_last_msg_id(msg_data.message_id, msg_data.chat.id)

	if msg_data.media_group_id:
		return

	forwarded_from_str = str(msg_data.forward_from_chat.id) if msg_data.forward_from_chat else None
	if not forwarded_from_str or forwarded_from_str not in DISCUSSION_CHAT_DATA:
		return

	discussion_chat_id = DISCUSSION_CHAT_DATA[forwarded_from_str]
	if discussion_chat_id != msg_data.chat.id:
		return

	main_channel = msg_data.forward_from_chat
	main_message_id = msg_data.forward_from_message_id
	discussion_message_id = msg_data.message_id

	db_utils.insert_or_update_discussion_message(main_message_id, main_channel.id, discussion_message_id)

	msg_data.chat = main_channel
	msg_data.message_id = msg_data.id = main_message_id

	edited_post = post_link_utils.add_link_to_new_post(msg_data)
	forwarding_utils.forward_and_add_inline_keyboard(bot, edited_post, new_ticket=True)


@bot.message_handler(func=lambda msg_data: msg_data.chat.id in DISCUSSION_CHAT_DATA.values(),
					 content_types=SUPPORTED_CONTENT_TYPES_COMMENT)
def handle_discussion_message(msg_data: telebot.types.Message):
	discussion_message_id = msg_data.message_id
	discussion_chat_id = msg_data.chat.id

	if msg_data.reply_to_message:
		comment_dispatcher.save_comment(bot, msg_data)

	db_utils.insert_or_update_last_msg_id(discussion_message_id, discussion_chat_id)


@bot.channel_post_handler(func=main_channel_filter, content_types=['new_chat_title'])
def handle_edit_channel_title(post_data: telebot.types.Message):
	if len(db_utils.get_main_channel_ids()) > 1:
		logging.info(f"Main channel {post_data.chat.id} name is changed")
		interval_updating_utils.start_interval_updating(bot)


@bot.edited_channel_post_handler(func=main_channel_filter, content_types=SUPPORTED_CONTENT_TYPES_TICKET)
def handle_edited_post(post_data: telebot.types.Message):
	if post_data.media_group_id:
		return

	"""
		After post is created in the main channel it will be edited by the telegram after it was copied to
		discussion channel and there is no way to determine if user edited the post or the telegram itself
		so if post was edited in first 5 seconds after it was created the notification will not be sent
	"""
	if (post_data.edit_date - post_data.date) > 5:
		utils.add_comment_to_ticket(bot, post_data, "A user edited the ticket.")

	post_link_utils.update_post_link(bot, post_data)
	forwarding_utils.forward_and_add_inline_keyboard(bot, post_data)


@bot.my_chat_member_handler()
def handle_bot_changed_permissions(member_update: telebot.types.ChatMemberUpdated):
	utils.bot_changed_permission(member_update, bot)


@bot.callback_query_handler(func=lambda call: main_channel_filter(call.message))
def handle_main_channel_keyboard_callback(call: telebot.types.CallbackQuery):
	if not utils.check_content_type(bot, call.message):
		return

	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call)
	elif call.data.startswith(post_link_utils.CALLBACK_PREFIX):
		post_link_utils.handle_callback(bot, call)
	elif call.data.startswith(scheduled_message_dispatcher.CALLBACK_PREFIX):
		scheduled_message_dispatcher.handle_callback(bot, call)


@bot.callback_query_handler(func=lambda call: subchannel_filter(call.message))
def handle_subchannel_keyboard_callback(call: telebot.types.CallbackQuery):
	if call.data.startswith(channel_manager.CALLBACK_PREFIX):
		channel_manager.handle_callback(bot, call)
		return

	main_message_data = db_utils.get_main_message_from_copied(call.message.message_id, call.message.chat.id)
	if main_message_data is None:
		logging.info(f"Button event in unknown message {[call.message.message_id, call.message.chat.id]}")
		return
	main_message_id, main_channel_id = main_message_data
	try:
		msg_data = utils.get_main_message_content_by_id(bot, main_channel_id, main_message_id)
	except ApiTelegramException:
		forwarding_utils.delete_main_message(bot, main_channel_id, main_message_id)
		return

	if not utils.check_content_type(bot, msg_data):
		forwarding_utils.delete_all_forwarded_messages(bot, main_channel_id, main_message_id)
		return

	subchannel_message_id = call.message.message_id
	subchannel_id = call.message.chat.id
	keyboard = call.message.reply_markup
	call.message = msg_data
	call.message.message_id = main_message_id
	call.message.chat.id = main_channel_id
	call.message.reply_markup = keyboard

	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call, subchannel_id, subchannel_message_id)
	if call.data.startswith(scheduled_message_dispatcher.CALLBACK_PREFIX):
		scheduled_message_dispatcher.handle_callback(bot, call, subchannel_id, subchannel_message_id)


@bot.callback_query_handler(func=lambda call: True)
def handle_individual_channel_keyboard_callback(call: telebot.types.CallbackQuery):
	if call.data.startswith(channel_manager.CALLBACK_PREFIX):
		channel_manager.handle_callback(bot, call)


@bot.message_handler(func=lambda msg: msg.text.startswith("/"), chat_types=["private"])
def handle_admin_bot_command(msg_data: telebot.types.Message):
	user_id = msg_data.from_user.id
	username = msg_data.from_user.username
	if username:
		username = f"@{username}"
	if user_id not in config_utils.ADMIN_USERS and username not in config_utils.ADMIN_USERS:
		return
	command_utils.handle_command(bot, msg_data)


@bot.channel_post_handler(func=lambda msg: msg.text.startswith("/"))
def handle_channel_bot_command(msg_data: telebot.types.Message):
	command_utils.handle_channel_command(bot, msg_data)


@bot.chat_member_handler(func=main_channel_filter)
def handler_check_new_member(member_update: telebot.types.ChatMemberUpdated):
	user_utils.check_new_member(member_update, bot)


@bot.chat_member_handler(func=subchannel_filter)
def handle_changed_permissions_subchannel(member_update: telebot.types.ChatMemberUpdated):
	user_utils.update_data_on_member_change(member_update, bot)
	chat_id = member_update.chat.id
	if db_utils.is_individual_channel_exists(chat_id):
		chat_admins = bot.get_chat_administrators(chat_id)
		chat_owner = next((user for user in chat_admins if type(user) == ChatMemberOwner), None)
		if not chat_owner:
			return
		owner_id = chat_owner.user.id
		db_utils.update_individual_channel_user(chat_id, owner_id)




bot.infinity_polling(allowed_updates=[
	"message",
	"edited_message",
	"channel_post",
	"edited_channel_post",
	"inline_query",
	"chosen_inline_result",
	"callback_query",
	"my_chat_member",
	"chat_member"
])
