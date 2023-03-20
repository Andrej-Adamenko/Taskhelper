import logging
import telebot

import forwarding_utils
import post_link_utils
import utils

CONFIG_FILE = "config.json"

BOT_TOKEN, CHANNEL_IDS, DUMP_CHAT_ID, SUBCHANNEL_DATA = utils.load_config(CONFIG_FILE)

CHAT_IDS_TO_IGNORE = forwarding_utils.get_all_subchannel_ids(SUBCHANNEL_DATA)
CHAT_IDS_TO_IGNORE.append(DUMP_CHAT_ID)

logging.basicConfig(format='%(asctime)s - %(levelname)s:%(message)s', level=logging.INFO)

bot = telebot.TeleBot(BOT_TOKEN)

channel_id_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS


@bot.channel_post_handler(func=channel_id_filter,
						  content_types=['audio', 'photo', 'voice', 'video', 'document', 'text'])
def handle_post(post_data):
	edited_post = post_link_utils.add_link_to_new_post(bot, post_data)
	hashtags = forwarding_utils.parse_hashtags(edited_post)
	if hashtags:
		forwarded_data = forwarding_utils.forward_to_subchannel(bot, edited_post, SUBCHANNEL_DATA, hashtags)
		forwarded_to, copied_message_id = forwarded_data if forwarded_data else [None, None]
		forwarding_utils.add_control_buttons(bot, edited_post, SUBCHANNEL_DATA, forwarded_to, copied_message_id, hashtags)


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
	else:
		CHANNEL_IDS.remove(chat_id)

	utils.update_config({"CHANNEL_IDS": CHANNEL_IDS}, CONFIG_FILE)


@bot.callback_query_handler(func=lambda call: channel_id_filter(call.message))
def handle_keyboard_callback(call: telebot.types.CallbackQuery):
	if call.data.startswith(forwarding_utils.CALLBACK_PREFIX):
		forwarding_utils.handle_callback(bot, call, SUBCHANNEL_DATA)
	elif call.data.startswith(post_link_utils.CALLBACK_PREFIX):
		post_link_utils.handle_callback(bot, call, DUMP_CHAT_ID, SUBCHANNEL_DATA)


bot.infinity_polling()
