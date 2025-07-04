from unittest import TestCase, main
from unittest.mock import Mock, patch, call

from pyrogram.types import InlineKeyboardMarkup
from telebot import TeleBot
from telebot.types import MessageEntity, Message, InlineKeyboardButton, Chat

import config_utils
from tests import test_helper
import utils
from tests.test_helper import create_mock_chat


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
		mock_chat = create_mock_chat(chat_id, "Test_message")
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_message.forward_from_chat = None
		mock_message.forward_from_message_id = message_id
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)
		self.assertNotEqual(result.chat, mock_chat)

	def test_get_message_content_by_id_forward_from_chat(self):
		mock_bot = Mock(spec=TeleBot)
		chat_id = -10012345678
		message_id = 125
		dump_chat_id = int(config_utils.DUMP_CHAT_ID)
		dump_message_id = 345
		mock_chat = create_mock_chat(chat_id, "Test_message")
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_message.forward_from_chat = mock_chat
		mock_message.forward_from_message_id = message_id
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)
		self.assertEqual(result.chat, mock_chat)

	def test_get_main_message_content_by_id(self):
		mock_bot = Mock(spec=TeleBot)
		chat_id = -10012345678
		message_id = 125
		dump_chat_id = int(config_utils.DUMP_CHAT_ID)
		dump_message_id = 345
		mock_chat = create_mock_chat(chat_id, "Test_message")
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_message.forward_from_chat = None
		mock_message.forward_from_message_id = message_id
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_main_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)
		self.assertNotEqual(result.chat, mock_chat)

	def test_get_main_message_content_by_id_forward_from_chat(self):
		mock_bot = Mock(spec=TeleBot)
		chat_id = -10012345678
		message_id = 125
		dump_chat_id = int(config_utils.DUMP_CHAT_ID)
		dump_message_id = 345
		mock_chat = create_mock_chat(chat_id, "Test_message")
		mock_message = test_helper.create_mock_message("", [], dump_chat_id, dump_message_id)
		mock_message.forward_from_chat = mock_chat
		mock_message.forward_from_message_id = message_id
		mock_bot.forward_message.return_value = mock_message

		result = utils.get_main_message_content_by_id(mock_bot, chat_id, message_id)
		mock_bot.forward_message.assert_called_once_with(chat_id=dump_chat_id, from_chat_id=chat_id, message_id=message_id)
		mock_bot.delete_message.assert_called_once_with(chat_id=dump_chat_id, message_id=dump_message_id)
		self.assertEqual(result.chat.id, chat_id)
		self.assertEqual(result.message_id, message_id)
		self.assertEqual(result.id, message_id)
		self.assertEqual(result.chat, mock_chat)


@patch("utils.set_post_content")
@patch("utils.offset_entities")
@patch("utils.get_post_content", side_effect=lambda post_data:
				(post_data.text, utils.align_entities_to_utf8(post_data.text, post_data.entities)))
@patch("db_utils.get_main_channel_ids", return_value=[-10012345678, -10087654321])
class AddChanelIdToPostDataTest(TestCase):
	def test_add_channel_id_with_few_channels(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		url_channel_id = 12345678
		channel_name = "main_channel_item"
		message_id = 124
		text = f"{message_id}. test_message"
		new_text = f"{channel_name}.{message_id}. test_message"
		entities = [MessageEntity(type="text_link", offset=0, length=len(f"{message_id}"), url=f"https://t.me/c/{url_channel_id}/{message_id}")]
		mock_message = test_helper.create_mock_message(text, entities, -10087654321, 153)
		mock_message.chat.title = channel_name
		text, entities = mock_get_post_content.side_effect(mock_message)

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_called_once_with(mock_message)
		mock_offset_entities.assert_called_once_with(entities, len(channel_name) + 1, [0])
		mock_set_post_content.assert_called_once_with(mock_message, new_text, entities)
		self.assertEqual(mock_message.entities[0].length, len(f"{channel_name}.{message_id}"))

	def test_add_channel_id_with_one_channel(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		url_channel_id = 12345678
		channel_name = "main_channel_item"
		message_id = 124
		text = f"{message_id}. test_message"
		entities = [MessageEntity(type="text_link", offset=0, length=len(f"{message_id}"), url=f"https://t.me/c/{url_channel_id}/{message_id}")]
		mock_message = test_helper.create_mock_message(text, entities, -10087654321, 153)
		mock_message.chat.title = channel_name
		mock_get_main_channel_ids.return_value = [-10012345678]

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_not_called()
		mock_offset_entities.assert_not_called()
		mock_set_post_content.assert_not_called()
		self.assertEqual(mock_message.entities[0].length, len(f"{message_id}"))

	def test_add_no_channel_id(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		channel_id = -10087654321
		url_channel_id = 87654321
		channel_name = "main_channel_item"
		message_id = 124
		text = f"{message_id}. test_message"
		new_text = f"{channel_name}.{message_id}. test_message"
		entities = [MessageEntity(type="text_link", offset=0, length=len(f"{message_id}"), url=f"https://t.me/c/{url_channel_id}/{message_id}")]
		mock_message = test_helper.create_mock_message(text, entities, channel_id, 153)
		mock_message.chat.title = channel_name
		text, entities = mock_get_post_content.side_effect(mock_message)

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_called_once_with(mock_message)
		mock_offset_entities.assert_called_once_with(entities, len(channel_name) + 1, [0])
		mock_set_post_content.assert_called_once_with(mock_message, new_text, entities)
		self.assertEqual(mock_message.entities[0].length, len(f"{channel_name}.{message_id}"))

	def test_add_exist_channel_id(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		channel_id = -10087654321
		url_channel_id = 87654321
		channel_name = "main_channel_item"
		message_id = 124
		text = f"{channel_name}.{message_id}. test_message"
		entities = [MessageEntity(type="text_link", offset=0, length=len(f"{channel_name}.{message_id}"), url=f"https://t.me/c/{url_channel_id}/{message_id}")]
		mock_message = test_helper.create_mock_message(text, entities, channel_id, 153)
		mock_message.chat.title = channel_name
		text, entities = mock_get_post_content.side_effect(mock_message)

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_called_once_with(mock_message)
		mock_offset_entities.assert_not_called()
		mock_set_post_content.assert_called_once_with(mock_message, text, entities)
		self.assertEqual(mock_message.entities[0].length, len(f"{channel_name}.{message_id}"))

	def test_no_entity_on_ticket_id(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		message_id = 124
		channel_name = "main_channel_item"
		text = f"{message_id}. test_message #cc"
		entities = [MessageEntity(type="hashtag", offset=25, length=len("#cc"), url="#cc")]
		mock_message = test_helper.create_mock_message(text, entities, -10087654321, 153)
		mock_message.chat.title = channel_name
		text, entities = mock_get_post_content.side_effect(mock_message)

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_called_once_with(mock_message)
		mock_offset_entities.assert_not_called()
		mock_set_post_content.assert_called_once_with(mock_message, text, entities)
		self.assertEqual(mock_message.entities[0].length, len("#cc"))

	def test_no_channel_in_channel_ids(self, mock_get_main_channel_ids, mock_get_post_content,
						  mock_offset_entities, mock_set_post_content, *args):
		url_channel_id = 12345678
		channel_name = "main_channel_item"
		message_id = 124
		text = f"{message_id}. test_message"
		entities = [MessageEntity(type="text_link", offset=0, length=len(f"{message_id}"), url=f"https://t.me/c/{url_channel_id}/{message_id}")]
		mock_message = test_helper.create_mock_message(text, entities, -10087654546, 153)
		mock_message.chat.title = channel_name

		utils.add_channel_id_to_post_data(mock_message)
		mock_get_main_channel_ids.assert_called_once_with()
		mock_get_post_content.assert_not_called()
		mock_offset_entities.assert_not_called()
		mock_set_post_content.assert_not_called()
		self.assertEqual(mock_message.entities[0].length, len(f"{message_id}"))


class GetForwardedFromIdTest(TestCase):
	def test_forward_from_chat(self, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		mock_message.forward_from_chat = Mock(id=channel_id)
		self.assertEqual(utils.get_forwarded_from_id(mock_message), channel_id)

	def test_forward_from(self, *args):
		user_id = 15645
		mock_message = test_helper.create_mock_message("", [])
		mock_message.forward_from_chat = None
		mock_message.forward_from = Mock(id=user_id)
		self.assertEqual(utils.get_forwarded_from_id(mock_message), user_id)

	def test_no_forward(self, *args):
		mock_message = test_helper.create_mock_message("", [])
		mock_message.forward_from_chat = None
		mock_message.forward_from = None
		self.assertEqual(utils.get_forwarded_from_id(mock_message), None)

	def test_default(self, *args):
		default = 56486
		mock_message = test_helper.create_mock_message("", [])
		mock_message.forward_from_chat = None
		mock_message.forward_from = None
		self.assertEqual(utils.get_forwarded_from_id(mock_message, default), default)


class CheckBotPermissionForMessagesTest(TestCase):
	def test_member_channel(self):
		mock_member = Mock(status="member", can_post_messages=True, can_edit_messages=True)
		mock_chat = Mock(type="channel", permissions=Mock(can_send_message=None))
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="member", can_post_messages=None, can_edit_messages=None)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="creator", can_post_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_post_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_post_messages=False, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_post_messages=True, can_edit_messages=False,)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_post_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="left", can_post_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="kicked", can_post_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

	def test_member_group(self):
		mock_member = Mock(status="member", can_send_messages=True, can_edit_messages=True)
		mock_chat = Mock(type="group", permissions=Mock(can_send_message=None))
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="member", can_send_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="creator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=False, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=False)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="left", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="kicked", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

	def test_member_group_no_send_message(self):
		mock_member = Mock(status="member", can_send_messages=True, can_edit_messages=True)
		mock_chat = Mock(type="group", permissions=Mock(can_send_messages=False))
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="member", can_send_messages=None, can_edit_messages=None)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="creator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=False, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=False)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="left", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="kicked", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

	def test_another_type(self):
		mock_member = Mock(status="member", can_send_messages=True, can_edit_messages=True)
		mock_chat = Mock(type="private", permissions=Mock(can_send_messages=False))
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="member", can_send_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="creator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=False, can_edit_messages=True)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=True, can_edit_messages=False)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="administrator", can_send_messages=None, can_edit_messages=None)
		self.assertTrue(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="left", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))

		mock_member = Mock(status="kicked", can_send_messages=True, can_edit_messages=True)
		self.assertFalse(utils.check_bot_permission_for_messages(mock_member, mock_chat))


@patch("config_utils.DISCUSSION_CHAT_DATA", {"-10012345678": -10087654321})
@patch("db_utils.delete_individual_channel")
@patch("db_utils.is_individual_channel_exists")
@patch("logging.info")
@patch("utils.get_key_by_value", side_effect=lambda dict, channel_id: "-10012345678" if channel_id in [-10087654321, -10012365478] else None)
@patch("user_utils.send_member_tags")
@patch("channel_manager.initialize_channel")
@patch("time.sleep")
@patch("utils.check_bot_permission_for_messages", side_effect=lambda member, chat: chat.id in [-10012345678, -10087654321] and member.status not in ['left', 'kicked'])
@patch("user_utils.update_data_on_member_change")
class BotChangedPermissionTest(TestCase):
	def test_add_with_permissions(self, mock_update_data_on_member_change, mock_check_bot_permission_for_messages,
								  mock_sleep, mock_initialize_channel, mock_send_member_tags, mock_get_key_by_value,
								  mock_info, mock_is_individual_channel_exists, mock_delete_individual_channel, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012345678
		mock_chat = Mock(id=channel_id)
		user_id = 12565
		mock_user = Mock(id=user_id)
		old_status = "left"
		mock_old_member = Mock(status=old_status)
		new_status = "member"
		mock_new_member = Mock(status=new_status)
		mock_member = Mock(new_chat_member=mock_new_member, old_chat_member=mock_old_member, chat=mock_chat, from_user=mock_user)

		utils.bot_changed_permission(mock_member, mock_bot)
		mock_update_data_on_member_change.assert_called_once_with(mock_member, mock_bot)
		mock_check_bot_permission_for_messages.assert_called_once_with(mock_new_member, mock_chat)
		mock_sleep.assert_called_once_with(1)
		mock_initialize_channel.assert_called_once_with(mock_bot, channel_id, user_id=user_id)
		mock_send_member_tags.assert_called_once_with(channel_id, mock_bot)
		mock_get_key_by_value.assert_called_once_with(config_utils.DISCUSSION_CHAT_DATA, channel_id)
		mock_info.assert_called_once_with(f"Bot received permissions for channel {channel_id}")
		mock_is_individual_channel_exists.assert_not_called()
		mock_delete_individual_channel.assert_not_called()

	def test_add_to_description_with_permissions(self, mock_update_data_on_member_change, mock_check_bot_permission_for_messages,
												 mock_sleep, mock_initialize_channel, mock_send_member_tags, mock_get_key_by_value,
												 mock_info, mock_is_individual_channel_exists, mock_delete_individual_channel, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10087654321
		main_channel_id = -10012345678
		mock_chat = Mock(id=channel_id)
		user_id = 12565
		mock_user = Mock(id=user_id)
		old_status = "left"
		mock_old_member = Mock(status=old_status)
		new_status = "member"
		mock_new_member = Mock(status=new_status)
		mock_member = Mock(new_chat_member=mock_new_member, old_chat_member=mock_old_member, chat=mock_chat, from_user=mock_user)

		utils.bot_changed_permission(mock_member, mock_bot)
		mock_update_data_on_member_change.assert_called_once_with(mock_member, mock_bot)
		mock_check_bot_permission_for_messages.assert_called_once_with(mock_new_member, mock_chat)
		mock_sleep.assert_called_once_with(1)
		mock_initialize_channel.assert_called_once_with(mock_bot, channel_id, user_id=user_id)
		mock_send_member_tags.assert_has_calls([call(channel_id, mock_bot), call(main_channel_id, mock_bot)])
		self.assertEqual(mock_send_member_tags.call_count, 2)
		mock_get_key_by_value.assert_called_once_with(config_utils.DISCUSSION_CHAT_DATA, channel_id)
		mock_info.assert_called_once_with(f"Bot received permissions for channel {channel_id}")
		mock_is_individual_channel_exists.assert_not_called()
		mock_delete_individual_channel.assert_not_called()

	def test_add_without_permissions(self, mock_update_data_on_member_change, mock_check_bot_permission_for_messages, mock_sleep,
									 mock_initialize_channel, mock_send_member_tags, mock_get_key_by_value, mock_info,
									 mock_is_individual_channel_exists, mock_delete_individual_channel, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10087456321
		mock_chat = Mock(id=channel_id)
		user_id = 12565
		mock_user = Mock(id=user_id)
		old_status = "left"
		mock_old_member = Mock(status=old_status)
		new_status = "member"
		mock_new_member = Mock(status=new_status)
		mock_member = Mock(new_chat_member=mock_new_member, old_chat_member=mock_old_member, chat=mock_chat, from_user=mock_user)

		utils.bot_changed_permission(mock_member, mock_bot)
		mock_update_data_on_member_change.assert_called_once_with(mock_member, mock_bot)
		mock_check_bot_permission_for_messages.assert_called_once_with(mock_new_member, mock_chat)
		mock_sleep.assert_not_called()
		mock_initialize_channel.assert_not_called()
		mock_send_member_tags.assert_not_called()
		mock_get_key_by_value.assert_not_called()
		mock_info.assert_called_once_with(f"Bot permissions for channel {channel_id} was removed")
		mock_is_individual_channel_exists.assert_not_called()
		mock_delete_individual_channel.assert_not_called()

	def test_add_to_description_without_permissions(self, mock_update_data_on_member_change, mock_check_bot_permission_for_messages,
													mock_sleep, mock_initialize_channel, mock_send_member_tags, mock_get_key_by_value,
													mock_info, mock_is_individual_channel_exists, mock_delete_individual_channel, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012365478
		mock_chat = Mock(id=channel_id)
		user_id = 12565
		mock_user = Mock(id=user_id)
		old_status = "left"
		mock_old_member = Mock(status=old_status)
		new_status = "member"
		mock_new_member = Mock(status=new_status)
		mock_member = Mock(new_chat_member=mock_new_member, old_chat_member=mock_old_member, chat=mock_chat, from_user=mock_user)

		utils.bot_changed_permission(mock_member, mock_bot)
		mock_update_data_on_member_change.assert_called_once_with(mock_member, mock_bot)
		mock_check_bot_permission_for_messages.assert_called_once_with(mock_new_member, mock_chat)
		mock_sleep.assert_not_called()
		mock_initialize_channel.assert_not_called()
		mock_send_member_tags.assert_not_called()
		mock_get_key_by_value.assert_not_called()
		mock_info.assert_called_once_with(f"Bot permissions for channel {channel_id} was removed")
		mock_is_individual_channel_exists.assert_not_called()
		mock_delete_individual_channel.assert_not_called()

	def test_remove(self, mock_update_data_on_member_change, mock_check_bot_permission_for_messages, mock_sleep,
					mock_initialize_channel, mock_send_member_tags, mock_get_key_by_value, mock_info,
					mock_is_individual_channel_exists, mock_delete_individual_channel, *args):
		mock_bot = Mock(spec=TeleBot)
		channel_id = -10012365478
		mock_chat = Mock(id=channel_id)
		user_id = 12565
		mock_user = Mock(id=user_id)
		old_status = "member"
		mock_old_member = Mock(status=old_status)
		new_status = "left"
		mock_new_member = Mock(status=new_status)
		mock_member = Mock(new_chat_member=mock_new_member, old_chat_member=mock_old_member, chat=mock_chat, from_user=mock_user)

		utils.bot_changed_permission(mock_member, mock_bot)
		mock_update_data_on_member_change.assert_called_once_with(mock_member, mock_bot)
		mock_check_bot_permission_for_messages.assert_called_once_with(mock_new_member, mock_chat)
		mock_sleep.assert_not_called()
		mock_initialize_channel.assert_not_called()
		mock_send_member_tags.assert_not_called()
		mock_get_key_by_value.assert_not_called()
		mock_info.assert_called_once_with(f"Bot permissions for channel {channel_id} was removed")
		mock_is_individual_channel_exists.assert_called_once_with(channel_id)
		mock_delete_individual_channel.assert_called_once_with(channel_id)



if __name__ == "__main__":
	main()
