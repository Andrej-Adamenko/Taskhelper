import telebot, time
import utils, post_link_utils
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

CONFIG_FILE = "config.json"

BOT_TOKEN, CHANNEL_IDS, DUMP_CHAT_ID = utils.load_config(CONFIG_FILE)

bot = telebot.TeleBot(BOT_TOKEN)

channel_id_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS

@bot.channel_post_handler(func=channel_id_filter, content_types=['audio', 'photo', 'voice', 'video', 'document', 'text'])
def handle_post(post_data):
	#skip forwarded messages and messages without text
	if post_data.forward_from_chat or post_data.text == None:
		return

	post_link_utils.add_link_to_new_post(bot, post_data)

@bot.edited_channel_post_handler(func=channel_id_filter)
def handle_edited_post(post_data):
	if post_data.text == None:
		return

	post_link_utils.update_post_link(bot, post_data)

@bot.my_chat_member_handler()
def handle_changed_permissions(message):
	chat_id = message.chat.id
	if chat_id == DUMP_CHAT_ID:
		return

	has_permissions = message.new_chat_member.can_edit_messages and message.new_chat_member.can_post_messages

	if has_permissions and chat_id in CHANNEL_IDS:
		return # channel_id already added to config file

	if not has_permissions and chat_id not in CHANNEL_IDS:
		return # channel_id already remove from config file

	if has_permissions:
		CHANNEL_IDS.append(chat_id)

		keyboard_markup = InlineKeyboardMarkup()
		keyboard_markup.row_width = 2
		keyboard_markup.add(InlineKeyboardButton("Yes", callback_data="cb_yes"), InlineKeyboardButton("No", callback_data="cb_no"))
		bot.send_message(chat_id=chat_id, text="Do you want to start adding links to older posts? (This can take some time, bot will not respond until updating is complete)", reply_markup=keyboard_markup)
	else:
		CHANNEL_IDS.remove(chat_id)		

	utils.update_config({"CHANNEL_IDS": CHANNEL_IDS}, CONFIG_FILE)

@bot.callback_query_handler(func=lambda call:channel_id_filter(call.message))
def handle_keyboard_callback(call):
	chat_id = call.message.chat.id
	if call.data == "cb_yes":
		bot.delete_message(chat_id=chat_id, message_id=call.message.id)
		post_link_utils.start_updating_older_messages(bot, chat_id, DUMP_CHAT_ID)
	elif call.data == "cb_no":
		bot.delete_message(chat_id=chat_id, message_id=call.message.id)


bot.infinity_polling()
