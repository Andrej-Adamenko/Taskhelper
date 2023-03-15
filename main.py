import telebot, time
import utils, post_link_utils

CONFIG_FILE = "config.json"

BOT_TOKEN, CHANNEL_IDS, DUMP_CHAT_ID = utils.load_config(CONFIG_FILE)

bot = telebot.TeleBot(BOT_TOKEN)
BOT_ID = bot.get_me().id

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
	if message.chat.id == DUMP_CHAT_ID:
		return

	has_permissions = message.new_chat_member.can_edit_messages

	if has_permissions and message.chat.id in CHANNEL_IDS:
		return # channel_id already added to config file

	if not has_permissions and message.chat.id not in CHANNEL_IDS:
		return # channel_id already remove from config file

	if has_permissions:
		CHANNEL_IDS.append(message.chat.id)
		post_link_utils.start_updating_older_messages(bot, message.chat.id, DUMP_CHAT_ID)
	else:
		CHANNEL_IDS.remove(message.chat.id)		

	utils.update_config({"CHANNEL_IDS": CHANNEL_IDS}, CONFIG_FILE)


bot.infinity_polling()
