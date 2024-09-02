from unittest import TestCase, main
from unittest.mock import Mock, patch

from telebot import TeleBot
from telebot.types import MessageEntity, Message

import forwarding_utils
import test_helper
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


class DeleteMainMessageTest(TestCase):
	@patch("db_utils.get_copied_messages_from_main", return_value=[[22, 987654321]])
	@patch("db_utils.get_ticket_data", return_value=None)
	@patch("db_utils.delete_scheduled_message_main")
	@patch("forwarding_utils.delete_forwarded_message")
	def test_delete_message(self, mock_delete_forwarded_message, mock_delete_scheduled_message_main, *args):
		mock_bot = Mock(spec=TeleBot)
		main_channel_id = 12341234
		main_message_id = 123

		utils.delete_main_message(mock_bot, main_channel_id, main_message_id)
		mock_delete_scheduled_message_main.assert_called_once_with(main_message_id, main_channel_id)
		mock_delete_forwarded_message.assert_called_once_with(mock_bot, 987654321, 22)


if __name__ == "__main__":
	main()
