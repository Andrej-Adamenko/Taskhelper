import telebot
from telebot import types
import utils

BOT_TOKEN, CHANNEL_IDS = utils.load_config("config.json")
LINK_ENDING = ". "

bot = telebot.TeleBot(BOT_TOKEN)

channel_id_filter = lambda message_data: message_data.chat.id in CHANNEL_IDS

@bot.channel_post_handler(func=channel_id_filter, content_types=['audio', 'photo', 'voice', 'video', 'document', 'text'])
def handle_post(post_data):
	#skip forwarded messages and messages without text
	if post_data.forward_from_chat or post_data.text == None:
		return

	post_url = utils.get_post_url(post_data)
	inserted_link_text = str(post_data.message_id)

	updated_entities = utils.offset_entities(post_data.entities, len(inserted_link_text) + len(LINK_ENDING))
	updated_entities.append(types.MessageEntity(type="text_link", offset=0, length=len(inserted_link_text), url=post_url))

	edited_post_text = inserted_link_text + LINK_ENDING + post_data.text
	bot.edit_message_text(text=edited_post_text, chat_id=post_data.chat.id, message_id=post_data.message_id, entities=updated_entities)

@bot.edited_channel_post_handler(func=channel_id_filter)
def handle_edited_post(post_data):
	if post_data.text == None:
		return

	post_url = utils.get_post_url(post_data)
	inserted_link_text = str(post_data.message_id)

	new_entity_offset = len(inserted_link_text) + len(LINK_ENDING)

	previous_link = utils.get_previous_link(post_data, post_url)
	if previous_link:
		if post_data.text.startswith(inserted_link_text + LINK_ENDING):
			return # return if link is correct

		post_data.text = post_data.text[previous_link.length:]
		new_entity_offset -= previous_link.length
		if post_data.text.startswith(LINK_ENDING):
			post_data.text = post_data.text[len(LINK_ENDING):]
			new_entity_offset -= len(LINK_ENDING)

		post_data.entities.remove(previous_link)

	post_data.entities = utils.offset_entities(post_data.entities, new_entity_offset)
	post_data.entities.append(types.MessageEntity(type="text_link", offset=0, length=len(inserted_link_text), url=post_url))

	edited_post_text = inserted_link_text + LINK_ENDING + post_data.text
	bot.edit_message_text(text=edited_post_text, chat_id=post_data.chat.id, message_id=post_data.message_id, entities=post_data.entities)

bot.infinity_polling()
