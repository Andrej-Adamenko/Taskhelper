import telebot, utils, time
from telebot.types import MessageEntity
from telebot.apihelper import ApiTelegramException

LINK_ENDING = ". "

def get_post_url(post_data):
	channel_url = str(post_data.chat.id)[4:]
	return "https://t.me/c/{0}/{1}".format(channel_url, post_data.message_id)

def insert_link_into_post(bot, post_data, link_text, post_url, additional_offset=0):
	updated_entities = utils.offset_entities(post_data.entities, len(link_text) + len(LINK_ENDING) + additional_offset)
	updated_entities.append(MessageEntity(type="text_link", offset=0, length=len(link_text), url=post_url))

	edited_post_text = link_text + LINK_ENDING + post_data.text
	bot.edit_message_text(text=edited_post_text, chat_id=post_data.chat.id, message_id=post_data.message_id, entities=updated_entities)	

def add_link_to_new_post(bot, post_data):
	post_url = get_post_url(post_data)
	link_text = str(post_data.message_id)

	insert_link_into_post(bot, post_data, link_text, post_url)

def update_post_link(bot, post_data):
	post_url = get_post_url(post_data)
	link_text = str(post_data.message_id)

	entity_offset = 0

	previous_link = utils.get_previous_link(post_data, post_url)
	if previous_link:
		if post_data.text.startswith(link_text + LINK_ENDING):
			return # return if link is correct
		entity_offset = remove_previous_link(post_data, previous_link)

	insert_link_into_post(bot, post_data, link_text, post_url, entity_offset)

def remove_previous_link(post_data, previous_link):
	entity_offset = 0

	post_data.text = post_data.text[previous_link.length:]
	entity_offset -= previous_link.length
	if post_data.text.startswith(LINK_ENDING):
		post_data.text = post_data.text[len(LINK_ENDING):]
		entity_offset -= len(LINK_ENDING)

	post_data.entities.remove(previous_link)

	return entity_offset

def start_updating_older_messages(bot, channel_id, dump_chat_id):
	last_message = bot.send_message(chat_id=channel_id, text="Bot started checking older messages.")
	current_msg_id = last_message.id - 1
	while current_msg_id > 0:
		time.sleep(1)

		forwarded_message = None
		try:
			forwarded_message = bot.forward_message(chat_id=dump_chat_id, from_chat_id=channel_id, message_id=current_msg_id)
		except ApiTelegramException:
			continue
		finally:
			current_msg_id -= 1

		bot.delete_message(chat_id=dump_chat_id, message_id=forwarded_message.message_id)

		if forwarded_message.forward_from_chat.id != channel_id:
			continue

		forwarded_message.message_id = forwarded_message.forward_from_message_id
		forwarded_message.chat = forwarded_message.forward_from_chat
		update_post_link(bot, forwarded_message)

