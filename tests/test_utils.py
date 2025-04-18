from unittest import TestCase, main
from unittest.mock import Mock

from pyrogram.types import InlineKeyboardMarkup
from telebot import TeleBot
from telebot.types import MessageEntity, Message, InlineKeyboardButton

import config_utils
from tests import test_helper
import utils


class GetPostContentTest(TestCase):
	def test_character_with_two_utf16_codepoints(self):
		post_data = Mock(spec=Message)
		post_data.text = "test 😁 #test asdf"
		post_data.caption = None
		post_data.entities = [MessageEntity(type="hashtag", offset=8, length=5)]

		text, entities = utils.get_post_content(post_data)
		updated_entity = entities[0]
		tag_text = text[updated_entity.offset:updated_entity.offset + updated_entity.length]
		self.assertEqual(tag_text, "#test")

	def test_multiple_characters_with_two_utf16_codepoints(self):
		post_data = Mock(spec=Message)
		post_data.text = "test #t1 😁 #t2 😁 #t3 asdf"
		post_data.caption = None
		post_data.entities = [
			MessageEntity(type="hashtag", offset=5, length=3),
			MessageEntity(type="hashtag", offset=12, length=3),
			MessageEntity(type="hashtag", offset=19, length=3),
		]

		text, entities = utils.get_post_content(post_data)
		tags = []
		for entity in entities:
			tags.append(text[entity.offset:entity.offset + entity.length])
		self.assertEqual(tags[0], "#t1")
		self.assertEqual(tags[1], "#t2")
		self.assertEqual(tags[2], "#t3")


class AlignEntitiesToUTF16Test(TestCase):
	def test_one_character_with_two_utf16_codepoints(self):
		text = "test 😁 #test asdf"
		entities = [MessageEntity(type="hashtag", offset=7, length=5)]
		entities[0].aligned_to_utf8 = True

		utils.align_entities_to_utf16(text, entities)
		self.assertEqual(entities[0].offset, 8)

	def test_multiple_characters_with_two_utf16_codepoints(self):
		text = "test #t1 😁 #t2 😁 #t3 asdf"
		entities = [
			MessageEntity(type="hashtag", offset=5, length=3),
			MessageEntity(type="hashtag", offset=11, length=3),
			MessageEntity(type="hashtag", offset=17, length=3),
		]
		entities[1].aligned_to_utf8 = True
		entities[2].aligned_to_utf8 = True

		utils.align_entities_to_utf16(text, entities)
		self.assertEqual(entities[0].offset, 5)
		self.assertEqual(entities[1].offset, 12)
		self.assertEqual(entities[2].offset, 19)


class IsPostDataEqualTest(TestCase):
	def test_phone_number_in_entities(self):
		text = "test 0991234567 test\n#o #bb #p2"
		entities1 = test_helper.create_hashtag_entity_list(text)
		entities2 = [MessageEntity(type="phone_number", offset=5, length=10)] + test_helper.create_hashtag_entity_list(text)

		post_data1 = test_helper.create_mock_message(text, entities1)
		post_data2 = test_helper.create_mock_message(text, entities2)

		self.assertTrue(utils.is_post_data_equal(post_data1, post_data2))

	def test_scheduled_tag_in_entities(self):
		scheduled_tag = "#s 2024-08-05 18:00"
		text = f"test test\n#o #bb #p2 {scheduled_tag}"
		entities1 = test_helper.create_hashtag_entity_list(text)
		entities2 = test_helper.create_hashtag_entity_list(text)
		entities2[-1].length = len(scheduled_tag)

		post_data1 = test_helper.create_mock_message(text, entities1)
		post_data2 = test_helper.create_mock_message(text, entities2)

		self.assertTrue(utils.is_post_data_equal(post_data1, post_data2))

	def test_different_entity_amount(self):
		text = f"test test\n#o #bb #p2"
		entities1 = test_helper.create_hashtag_entity_list(text)
		entities2 = test_helper.create_hashtag_entity_list(text)
		entities2.append(MessageEntity(type="hashtag", offset=17, length=3))

		post_data1 = test_helper.create_mock_message(text, entities1)
		post_data2 = test_helper.create_mock_message(text, entities2)

		self.assertFalse(utils.is_post_data_equal(post_data1, post_data2))

	def test_different_text(self):
		text1 = f"test test\n#o #bb #p2"
		text2 = f"asdf asdf\n#o #bb #p2"
		entities1 = test_helper.create_hashtag_entity_list(text1)
		entities2 = test_helper.create_hashtag_entity_list(text2)

		post_data1 = test_helper.create_mock_message(text1, entities1)
		post_data2 = test_helper.create_mock_message(text2, entities2)

		self.assertFalse(utils.is_post_data_equal(post_data1, post_data2))


class ReplaceWhitespacesTest(TestCase):
	def test_replace_whitespaces(self):
		text = "test 0991234567 test\n#o\xa0#bb\xa0#p2"
		result = utils.replace_whitespaces(text)
		self.assertEqual(result, "test 0991234567 test\n#o #bb #p2")

	def test_ignored_whitespace_characters(self):
		text = "test\t0991234567\tasdf\naaaa\n#o #bb #p2"
		result = utils.replace_whitespaces(text)
		self.assertEqual(result, text)

class MergeKeyboardMarkupTest(TestCase):
	def test_merge_empty_keyboards(self):
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = []

		mock_keyboard2 = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard2.keyboard = []

		result = utils.merge_keyboard_markup(mock_keyboard, mock_keyboard2)
		self.assertEqual(result.keyboard, [])

	def test_merge_empty_second_keyboard(self):
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [InlineKeyboardButton("Start")]

		mock_keyboard2 = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard2.keyboard = []

		result = utils.merge_keyboard_markup(mock_keyboard, mock_keyboard2)
		self.assertEqual(result.keyboard, mock_keyboard.keyboard)

	def test_merge_empty_first_keyboard(self):
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = []

		mock_keyboard2 = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard2.keyboard = [InlineKeyboardButton("Stop")]

		result = utils.merge_keyboard_markup(mock_keyboard, mock_keyboard2)
		self.assertEqual(result.keyboard, mock_keyboard2.keyboard)

	def test_merge_keyboards(self):
		mock_empty_button = Mock(spec=InlineKeyboardButton)
		mock_empty_button.text = ""
		mock_empty_button.callback_data = config_utils.EMPTY_CALLBACK_DATA_BUTTON

		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [InlineKeyboardButton("Start")]

		mock_keyboard2 = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard2.keyboard = [InlineKeyboardButton("Stop")]

		result = utils.merge_keyboard_markup(mock_keyboard, mock_keyboard2, empty_button=mock_empty_button)
		self.assertEqual(result.keyboard, mock_keyboard.keyboard + [[mock_empty_button]] + mock_keyboard2.keyboard)

	def test_merge_emtpy_button_keyboards(self):
		mock_keyboard = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard.keyboard = [InlineKeyboardButton("Start")]

		mock_keyboard2 = Mock(spec=InlineKeyboardMarkup)
		mock_keyboard2.keyboard = [InlineKeyboardButton("Stop")]

		result = utils.merge_keyboard_markup(mock_keyboard, mock_keyboard2, empty_button=None)
		self.assertEqual(result.keyboard, mock_keyboard.keyboard + mock_keyboard2.keyboard)


class GetMessageContentByIdTest(TestCase):
	def test_get_message_content_by_id(self):
		mock_bot = Mock(spec=TeleBot)
		chat_id = -10012345678
		message_id = 125
		dump_chat_id = int(config_utils.DUMP_CHAT_ID)
		dump_message_id = 345
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)

	def test_get_main_message_content_by_id(self):
		mock_bot = Mock(spec=TeleBot)
		chat_id = -10012345678
		message_id = 125
		dump_chat_id = int(config_utils.DUMP_CHAT_ID)
		dump_message_id = 345
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_main_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)





if __name__ == "__main__":
	main()
