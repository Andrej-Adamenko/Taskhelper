import telebot
from telebot import types
import utils

BOT_TOKEN, CHANNEL_IDS = utils.load_config("config.json")

bot = telebot.TeleBot(BOT_TOKEN)

channel_id_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS

@bot.channel_post_handler(func=channel_id_filter)
def handle_post(post_data):
	#skip forwarded messages
	if post_data.forward_from_chat:
		return

	post_url = utils.get_post_url(post_data)
	inserted_text = str(post_data.message_id) + ". "

	updated_entities = []
	if post_data.entities:
		updated_entities = post_data.entities
		for entity in updated_entities:
			entity.offset += len(inserted_text)

	updated_entities.append(types.MessageEntity(type="text_link", offset=0, length=len(inserted_text), url=post_url))
	edited_post_text = inserted_text + post_data.text
	bot.edit_message_text(text=edited_post_text, chat_id=post_data.chat.id, message_id=post_data.message_id, entities=updated_entities)

bot.infinity_polling()
