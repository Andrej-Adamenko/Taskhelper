from unittest import TestCase, main
from unittest.mock import patch, call, Mock

import telebot.types

import config_utils
import hashtag_data as hashtag_data_module
from hashtag_data import HashtagData
from tests import test_helper


@patch("copy.deepcopy", side_effect=lambda c: c)
@patch("hashtag_data.HashtagData.copy_tags_from_other_hashtags")
@patch("hashtag_data.HashtagData.remove_found_hashtags")
@patch("hashtag_data.HashtagData.insert_default_tags")
@patch("hashtag_data.HashtagData.is_status_missing", return_value=False)
@patch("hashtag_data.HashtagData.get_priority_number", return_value=1)
@patch("hashtag_data.HashtagData.get_assigned_user", return_value="aa")
@patch("hashtag_data.HashtagData.copy_users_from_text")
@patch("hashtag_data.HashtagData.extract_other_hashtags")
@patch("hashtag_data.HashtagData.extract_hashtags", return_value=(None, None, [], None))
@patch("hashtag_data.HashtagData.remove_strikethrough_entities")
@patch("hashtag_data.HashtagData.check_last_line")
@patch("hashtag_data.HashtagData.update_scheduled_tag_entities")
class InitTest(TestCase):
	def test_default(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)

		HashtagData(mock_message, main_channel_id)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_is_status_missing.assert_called_once_with()
		mock_insert_default_tags.assert_not_called()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()

	def test_invalid_user_tag(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)

		HashtagData(mock_message, main_channel_id, invalid_user_tag_to_default=True)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, True)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_is_status_missing.assert_called_once_with()
		mock_insert_default_tags.assert_not_called()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()

	def test_missing_tags(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_assigned_user.return_value = None
		mock_get_priority_number.return_value = None
		mock_is_status_missing.return_value = False

		HashtagData(mock_message, main_channel_id)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_not_called()
		mock_is_status_missing.assert_not_called()
		mock_insert_default_tags.assert_not_called()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()


	def test_missing_priority_number(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_priority_number.return_value = None

		HashtagData(mock_message, main_channel_id)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_is_status_missing.assert_not_called()
		mock_insert_default_tags.assert_not_called()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()

	def test_insert_default_tags(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)

		HashtagData(mock_message, main_channel_id, insert_default_tags=True)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_is_status_missing.assert_called_once_with()
		mock_insert_default_tags.assert_not_called()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()

	def test_insert_default_tags_missing_tags(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_assigned_user.return_value = None
		mock_get_priority_number.return_value = None
		mock_is_status_missing.return_value = False

		HashtagData(mock_message, main_channel_id, insert_default_tags=True)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_not_called()
		mock_is_status_missing.assert_not_called()
		mock_insert_default_tags.assert_called_once_with()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()


	def test_insert_default_tags_missing_priority_number(self, mock_update_scheduled_tag_entities, mock_check_last_line, mock_remove_strikethrough_entities,
					 mock_extract_hashtags, mock_extract_other_hashtags, mock_copy_users_from_text,
					 mock_get_assigned_user, mock_get_priority_number, mock_is_status_missing, mock_insert_default_tags,
					 mock_remove_found_hashtags, mock_copy_tags_from_other_hashtags, *args):
		main_channel_id = -10012345678
		main_message_id = 2165
		mock_message = test_helper.create_mock_message("", [], main_channel_id, main_message_id)
		mock_get_priority_number.return_value = None

		HashtagData(mock_message, main_channel_id, insert_default_tags=True)
		mock_update_scheduled_tag_entities.assert_called_once_with()
		mock_check_last_line.assert_called_once_with()
		mock_remove_strikethrough_entities.assert_called_once_with()
		mock_extract_hashtags.assert_called_once_with(mock_message, main_channel_id, False)
		mock_extract_other_hashtags.assert_called_once_with()
		mock_copy_users_from_text.assert_called_once_with()
		mock_get_assigned_user.assert_called_once_with()
		mock_get_priority_number.assert_called_once_with()
		mock_is_status_missing.assert_not_called()
		mock_insert_default_tags.assert_called_once_with()
		mock_remove_found_hashtags.assert_called_once_with()
		mock_copy_tags_from_other_hashtags.assert_called_once_with()



@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.OPENED_TAG", "o")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("user_utils.get_member_ids_channel", return_value=[1, 2, 3])
class FindCopyUsersFromText(TestCase):
	def test_find_mentioned_users(self, *args):
		config_utils.USER_TAGS = {"aa": 1, "bb": 2, "cc": 3}
		text = f"text #aa #bb\n#o #cc #p #user_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.hashtag_indexes = [None, 2, [3], 4]
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.user_tags = ["cc"]
		hashtag_data.post_data = post_data
		result = hashtag_data.copy_users_from_text()
		self.assertEqual(result, ["aa", "bb"])
		self.assertEqual(hashtag_data.user_tags, ["cc", "aa", "bb"])

	def test_no_mentioned_users(self, *args):
		config_utils.USER_TAGS = {"cc": 3}
		text = f"text test\n#o #cc #p #user_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.hashtag_indexes = [None, 0, [1], 2]
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.user_tags = ["cc"]
		hashtag_data.post_data = post_data
		result = hashtag_data.copy_users_from_text()
		self.assertEqual(result, [])
		self.assertEqual(hashtag_data.user_tags, ["cc"])

	def test_assign_user(self, mock_get_member_ids_channel, *args):
		config_utils.USER_TAGS = {"aa": 1, "bb": 2}
		mock_get_member_ids_channel.return_value = [2, 3]
		text = f"text #aa #bb test\n#o #p"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.hashtag_indexes = [None, 2, [], 3]
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.user_tags = []
		hashtag_data.post_data = post_data
		result = hashtag_data.copy_users_from_text()
		self.assertEqual(result, ["bb"])
		self.assertEqual(hashtag_data.user_tags, ["bb"])


class GetEntitiesToIgnoreTest(TestCase):
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_middle_and_back_entities(self, *args):
		text = f"text #aa #bb\n#o #cc #p #user_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(0, 2))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_front_entities(self, *args):
		text = f"#aa #bb test #cc test"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = False
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(2, 3))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_back_entities(self, *args):
		text = f"test text\n#o #cc #p #user_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(0, 0))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_middle_and_front_entities(self, *args):
		text = f"#o #cc #p test #aa #bb text"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = False
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(3, 5))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_end_of_line_entities(self, *args):
		text = f"#aa text #bb #user_tag"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = False
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(1, 3))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag")
	def test_other_tags_at_the_start(self, mock_is_service_tag, *args):
		service_hashtags = ["open", "aa", "bb", "p"]
		mock_is_service_tag.side_effect = lambda tag, a: tag in service_hashtags

		text = f"#test #open #aa #bb #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(0, 5))

	@patch("post_link_utils.is_ticket_number_entity", return_value=True)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag")
	def test_strikethrough_ticket_number(self, mock_is_service_tag, *args):
		service_hashtags = ["open", "aa", "bb", "p"]
		mock_is_service_tag.side_effect = lambda tag, a: tag in service_hashtags

		text = f"45. test\n #open #aa #bb #p1"
		entities = [
			telebot.types.MessageEntity(type="text_link", offset=0, length=2, url="https://t.me/c/1234567890/45"),
			telebot.types.MessageEntity(type="strikethrough", offset=0, length=2)
		]
		entities += test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 1234567890

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.post_data = post_data
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(2, 2))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_is_service_tag(self, mock_is_service_tag, *args):
		text = f"#test #open #aa #bb #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities)
		mock_is_service_tag.assert_has_calls([call("test", False), call("open", False), call("aa", False),
											  call("bb", False), call("p1", False)])
		self.assertEqual(result, range(5, 5))

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	def test_is_service_tag_all_user_tags(self, mock_is_service_tag, *args):
		text = f"#test #open #aa #bb #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.get_entities_to_ignore(text, entities, True)
		mock_is_service_tag.assert_has_calls([call("test", True), call("open", True), call("aa", True),
											  call("bb", True), call("p1", True)])
		self.assertEqual(result, range(5, 5))


@patch("user_utils.get_member_ids_channel", return_value = [12456, 5164, 34695])
@patch("config_utils.USER_TAGS", {"CC": 5164, "DD": 16835})
@patch("hashtag_data.OPENED_TAG", "open")
@patch("hashtag_data.CLOSED_TAG", "closed")
@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.SCHEDULED_TAG", "sch")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
class IsServiceTagTest(TestCase):
	def test_result(self, *args):
		channel_id = -10087461354
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id

		self.assertTrue(hashtag_data.is_service_tag("sch 2025-03-12"))
		self.assertTrue(hashtag_data.is_service_tag("sch"))
		self.assertTrue(hashtag_data.is_service_tag("p1"))
		self.assertFalse(hashtag_data.is_service_tag("p4"))
		self.assertTrue(hashtag_data.is_service_tag("open"))
		self.assertTrue(hashtag_data.is_service_tag("closed"))
		self.assertTrue(hashtag_data.is_service_tag("CC"))
		self.assertFalse(hashtag_data.is_service_tag("DD"))
		self.assertFalse(hashtag_data.is_service_tag("DD", False))
		self.assertTrue(hashtag_data.is_service_tag("DD", True))
		self.assertFalse(hashtag_data.is_service_tag("AA"))

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_scheduled_tag(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "sch 2025-03-12"

		hashtag_data.is_service_tag(tag)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_not_called()
		mock_check_user_tag.assert_not_called()

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_priority_tag(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "p1"

		hashtag_data.is_service_tag(tag)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_called_once_with(tag, hashtag_data_module.PRIORITY_TAG)
		mock_check_user_tag.assert_not_called()

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_opened_tag(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "open"

		hashtag_data.is_service_tag(tag)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_called_once_with(tag, hashtag_data_module.PRIORITY_TAG)
		mock_check_user_tag.assert_not_called()

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_closed_tag(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "closed"

		hashtag_data.is_service_tag(tag)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_called_once_with(tag, hashtag_data_module.PRIORITY_TAG)
		mock_check_user_tag.assert_not_called()

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_user_tag(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "CC"

		hashtag_data.is_service_tag(tag)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_called_once_with(tag, hashtag_data_module.PRIORITY_TAG)
		mock_check_user_tag.assert_called_once_with(tag, channel_id)

	@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: tag in config_utils.USER_TAGS)
	@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, priority: tag.startswith(priority))
	@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, schedule: tag.startswith(schedule))
	def test_user_tag_all_tags(self, mock_check_scheduled_tag, mock_check_priority_tag, mock_check_user_tag, *args):
		channel_id = -10012345678
		mock_message = test_helper.create_mock_message("", [])
		hashtag_data = HashtagData(mock_message, channel_id)
		hashtag_data.main_channel_id = channel_id
		tag = "CC"

		hashtag_data.is_service_tag(tag, True)
		mock_check_scheduled_tag.assert_called_once_with(tag, hashtag_data_module.SCHEDULED_TAG)
		mock_check_priority_tag.assert_called_once_with(tag, hashtag_data_module.PRIORITY_TAG)
		mock_check_user_tag.assert_called_once_with(tag, None)



@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("hashtag_data.HashtagData.update_scheduled_tag_entity_length")
@patch("hashtag_data.HashtagData.get_entities_to_ignore")

@patch("hashtag_data.HashtagData.check_old_scheduled_tag", side_effect=lambda tag: (tag.startswith("sch ") or tag == "sch"))
@patch("hashtag_data.HashtagData.check_scheduled_tag", side_effect=lambda tag, sch_tag: (tag.startswith(f"{sch_tag} ") or tag == sch_tag))
@patch("hashtag_data.HashtagData.check_old_status_tag", side_effect=lambda tag: (tag == "open" or tag == "closed"))
@patch("hashtag_data.HashtagData.check_user_tag", side_effect=lambda tag, channel_id: (tag in ["CC", "DD", "AA"] and channel_id is None or tag in ["CC", "DD"]))
@patch("hashtag_data.HashtagData.check_old_priority_tag", side_effect=lambda tag: (tag.startswith("p")))
@patch("hashtag_data.HashtagData.check_priority_tag", side_effect=lambda tag, p_tag: (tag.startswith(p_tag)))
class FindHashtagIndexes(TestCase):
	def setUp(self):
		hashtag_data_module.OPENED_TAG = "open"
		hashtag_data_module.CLOSED_TAG = "closed"
		hashtag_data_module.PRIORITY_TAG = "p"
		hashtag_data_module.SCHEDULED_TAG = "sch"
		config_utils.USER_TAGS = {"CC": 5164, "DD": 16835, "AA": 1654}

	def test_all_tags(self, mock_check_priority_tag, mock_check_old_priority_tag, mock_check_user_tag,
					  mock_check_old_status_tag, mock_check_scheduled_tag, mock_check_old_scheduled_tag,
					  mock_get_entities_to_ignore, mock_update_scheduled_tag_entity_length, *args):
		main_channel_id = -10087654321
		tags = ["sch", "AA", "CC", "p2", "closed", "open"]
		text = "#open #closed #p2 #CC #AA #sch 2025-12-10"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_entities_to_ignore.return_value = []

		manager = Mock()
		manager.attach_mock(mock_check_old_scheduled_tag, "a")
		manager.attach_mock(mock_check_scheduled_tag, "b")
		manager.attach_mock(mock_check_old_status_tag, "c")
		manager.attach_mock(mock_check_user_tag, "d")
		manager.attach_mock(mock_check_old_priority_tag, "e")
		manager.attach_mock(mock_check_priority_tag, "f")
		expected_calls = [
			call.a(tags[0]),

			call.a(tags[1]), call.b(tags[1], hashtag_data_module.SCHEDULED_TAG), call.c(tags[1]), call.d(tags[1], main_channel_id),
			call.e(tags[1]), call.f(tags[1], hashtag_data_module.PRIORITY_TAG),

			call.a(tags[2]), call.b(tags[2], hashtag_data_module.SCHEDULED_TAG), call.c(tags[2]), call.d(tags[2], main_channel_id),

			call.a(tags[3]), call.b(tags[3], hashtag_data_module.SCHEDULED_TAG), call.c(tags[3]), call.d(tags[3], main_channel_id),
			call.e(tags[3]),

			call.a(tags[4]), call.b(tags[4], hashtag_data_module.SCHEDULED_TAG), call.c(tags[4]),

			call.a(tags[5]), call.b(tags[5], hashtag_data_module.SCHEDULED_TAG), call.c(tags[5])
		]

		hashtag_data = HashtagData()
		result = hashtag_data.find_hashtag_indexes(text, entities, main_channel_id)
		mock_update_scheduled_tag_entity_length.assert_has_calls([call(text, entities, 0), call(text, entities, 1),
																  call(text, entities, 2), call(text, entities, 3),
																  call(text, entities, 4), call(text, entities, 5)])
		mock_get_entities_to_ignore.assert_called_once_with(text, entities, False)
		self.assertEqual(manager.mock_calls, expected_calls)
		self.assertEqual(result, (5, 0, [3], 2))

	def test_all_user_tags(self, mock_check_priority_tag, mock_check_old_priority_tag, mock_check_user_tag,
					  mock_check_old_status_tag, mock_check_scheduled_tag, mock_check_old_scheduled_tag,
					  mock_get_entities_to_ignore, mock_update_scheduled_tag_entity_length, *args):
		main_channel_id = -10087654321
		tags = ["sch", "AA", "CC", "p2", "closed", "open"]
		text = "#open #closed #p2 #CC #AA #sch 2025-12-10"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_entities_to_ignore.return_value = []

		manager = Mock()
		manager.attach_mock(mock_check_old_scheduled_tag, "a")
		manager.attach_mock(mock_check_scheduled_tag, "b")
		manager.attach_mock(mock_check_old_status_tag, "c")
		manager.attach_mock(mock_check_user_tag, "d")
		manager.attach_mock(mock_check_old_priority_tag, "e")
		manager.attach_mock(mock_check_priority_tag, "f")
		expected_calls = [
			call.a(tags[0]),

			call.a(tags[1]), call.b(tags[1], hashtag_data_module.SCHEDULED_TAG), call.c(tags[1]), call.d(tags[1], None),

			call.a(tags[2]), call.b(tags[2], hashtag_data_module.SCHEDULED_TAG), call.c(tags[2]), call.d(tags[2], None),

			call.a(tags[3]), call.b(tags[3], hashtag_data_module.SCHEDULED_TAG), call.c(tags[3]), call.d(tags[3], None),
			call.e(tags[3]),

			call.a(tags[4]), call.b(tags[4], hashtag_data_module.SCHEDULED_TAG), call.c(tags[4]),

			call.a(tags[5]), call.b(tags[5], hashtag_data_module.SCHEDULED_TAG), call.c(tags[5])
		]

		hashtag_data = HashtagData()
		result = hashtag_data.find_hashtag_indexes(text, entities, main_channel_id, True)
		mock_update_scheduled_tag_entity_length.assert_has_calls([call(text, entities, 0), call(text, entities, 1),
																  call(text, entities, 2), call(text, entities, 3),
																  call(text, entities, 4), call(text, entities, 5)])
		mock_get_entities_to_ignore.assert_called_once_with(text, entities, True)
		self.assertEqual(manager.mock_calls, expected_calls)
		self.assertEqual(result, (5, 0, [3, 4], 2))


@patch("user_utils.get_user_tags", return_value={"aa": 1356, "bb": 156, "cc": 56846})
class RemoveDuplicatesTest(TestCase):
	priority_side_effect = lambda text, entities: (text, entities)
	status_side_effect = lambda text, entities: (text, entities)

	@patch("hashtag_data.HashtagData.remove_redundant_priority_tags", side_effect=priority_side_effect)
	@patch("hashtag_data.HashtagData.remove_redundant_status_tags", side_effect=status_side_effect)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_remove_user_tag_duplicates(self, *args):
		text = f"text\n#aa #bb #cc #aa #bb"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.is_sent = False
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_duplicates(post_data)
		self.assertEqual(result.text, "text\n#aa #bb #cc")


@patch("user_utils.get_user_tags", return_value={"aa": 1356, "bb": 156, "cc": 56846})
@patch("hashtag_data.POSSIBLE_PRIORITIES", ["1", "2", "3"])
@patch("hashtag_data.PRIORITY_TAG", "p")
class RemoveRedundantPriorityTagsTest(TestCase):
	@patch("hashtag_data.HashtagData.get_priority_number_or_default", return_value="1")
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_same_priority_tags(self, *args):
		text = f"text\n#aa #bb #p1 #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.hashtag_indexes = [None, None, [0, 1], 2]
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_priority_tags(text, entities)
		self.assertEqual(result[0], f"text\n#aa #bb #p1")

	@patch("hashtag_data.HashtagData.get_priority_number_or_default", return_value="1")
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_different_priority_tags(self, *args):
		text = f"text\n#aa #bb #p2 #p3 #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.hashtag_indexes = [None, None, [0, 1], 2]
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_priority_tags(text, entities)
		self.assertEqual(result[0], f"text\n#aa #bb #p1")

	@patch("hashtag_data.HashtagData.get_priority_number_or_default", return_value=None)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_no_default_priority_tag(self, *args):
		text = f"text\n#aa #bb #p"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.hashtag_indexes = [None, None, [0, 1], 2]
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_priority_tags(text, entities)
		self.assertEqual(result[0], f"text\n#aa #bb #p")


@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.OPENED_TAG", "o")
@patch("hashtag_data.CLOSED_TAG", "x")
class RemoveRedundantStatusTagsTest(TestCase):
	@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_same_status_tags(self, *args):
		text = f"text\n#o #o #aa #bb #p1 #o"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_status_tags(text, entities)
		self.assertEqual(result[0], f"text\n#o #aa #bb #p1")

	@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_different_status_tags(self, *args):
		text = f"text\n#x #o #x #aa #bb #p1"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_status_tags(text, entities)
		self.assertEqual(result[0], f"text\n#o #aa #bb #p1")


@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.OPENED_TAG", "o")
@patch("hashtag_data.CLOSED_TAG", "x")
@patch("hashtag_data.SCHEDULED_TAG", "s")
class RemoveRedundantScheduledTagsTest(TestCase):
	def update_scheduled_tag_entities_length(self, scheduled_tag, text, entities):
		for entity in entities:
			entity_text = text[entity.offset : entity.offset + entity.length]
			if entity_text != scheduled_tag:
				continue

			text_after_tag = text[entity.offset:]
			scheduled_tag_parts = text_after_tag.split(" ")[:3]
			if len(scheduled_tag_parts) < 3:
				continue
			full_tag_length = len(" ".join(scheduled_tag_parts))
			entity.length = full_tag_length

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_identical_scheduled_tags(self, *args):
		text = "text\n#o #aa #bb #p1 #s 2023-06-25 17:00 #s 2023-06-25 17:00"
		entities = test_helper.create_hashtag_entity_list(text)
		self.update_scheduled_tag_entities_length("#s", text, entities)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.scheduled_tag = None
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_scheduled_tags(text, entities)
		self.assertEqual(result[0], "text\n#o #aa #bb #p1 #s 2023-06-25 17:00")

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_scheduled_tags_without_date(self, *args):
		text = "text\n#o #aa #bb #p1 #s #s"
		entities = test_helper.create_hashtag_entity_list(text)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_scheduled_tags(text, entities)
		self.assertEqual(result[0], "text\n#o #aa #bb #p1")
		self.assertIsNone(hashtag_data.scheduled_tag)

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	def test_partial_scheduled_tag(self, *args):
		text = "text\n#o #aa #bb #p1 #s 2023-06-25"
		entities = test_helper.create_hashtag_entity_list(text)
		self.update_scheduled_tag_entities_length("#s", text, entities)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_scheduled_tags(text, entities)
		self.assertEqual(result[0], "text\n#o #aa #bb #p1 #s 2023-06-25")

	@patch("hashtag_data.HashtagData.__init__", return_value=None)
	@patch("hashtag_data.HashtagData.get_scheduled_timestamp", return_value=1687701600)
	def test_user_tag_at_the_end(self, *args):
		text = "text\n#o #aa #bb #p1 #s 2023-06-25 17:00 #test"
		entities = test_helper.create_hashtag_entity_list(text)
		self.update_scheduled_tag_entities_length("#s", text, entities)
		post_data = test_helper.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_scheduled_tags(text, entities)
		self.assertEqual(result[0], "text\n#o #aa #bb #p1 #s 2023-06-25 17:00 #test")


@patch("hashtag_data.SCHEDULED_TAG", "s")
class UpdateScheduledTagTest(TestCase):
	def test_update_entity(self, *args):
		text = "#s 2023-06-25 17:00"
		entities = test_helper.create_hashtag_entity_list(text)

		result = HashtagData.update_scheduled_tag_entity_length(text, entities, 0)
		self.assertTrue(result)
		self.assertEqual(entities[0].length, len(text))

	def test_not_scheduled_tag(self, *args):
		text = "#test 2023-06-25 17:00"
		entities = test_helper.create_hashtag_entity_list(text)

		entity_length = entities[0].length
		result = HashtagData.update_scheduled_tag_entity_length(text, entities, 0)
		self.assertFalse(result)
		self.assertEqual(entities[0].length, entity_length)

	def test_incomplete_scheduled_tag(self, *args):
		text = "#s 2023-06-25"
		entities = test_helper.create_hashtag_entity_list(text)

		result = HashtagData.update_scheduled_tag_entity_length(text, entities, 0)
		self.assertFalse(result)
		self.assertEqual(entities[0].length, len(text))

	def test_new_line_after_scheduled_tag(self, *args):
		scheduled_tag = "#s 2023-06-25 22:00"
		text = f"test {scheduled_tag}\ntext test"
		entities = test_helper.create_hashtag_entity_list(text)

		result = HashtagData.update_scheduled_tag_entity_length(text, entities, 0)
		self.assertTrue(result)
		self.assertEqual(entities[0].length, len(scheduled_tag))


@patch("hashtag_data.POSSIBLE_PRIORITIES", ["1", "2", "3"])
@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.OPENED_TAG", "o")
@patch("hashtag_data.CLOSED_TAG", "x")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
class CopyTagsFromOtherTagsTest(TestCase):
	def test_multiple_priority_tags(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.scheduled_tag = None
		hashtag_data.status_tag = None
		hashtag_data.priority_tag = None
		hashtag_data.other_hashtags = ["#p2", "#p3", "#p1", "#p2"]

		hashtag_data.copy_tags_from_other_hashtags()
		self.assertEqual(hashtag_data.priority_tag, "p1")

	@patch("hashtag_data.HashtagData.get_priority_number_or_default", return_value=None)
	def test_default_priority_higher_than_found_priority(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.scheduled_tag = None
		hashtag_data.status_tag = None
		hashtag_data.priority_tag = "p1"
		hashtag_data.other_hashtags = ["#p2", "#p3", "#p2"]

		hashtag_data.copy_tags_from_other_hashtags()
		self.assertEqual(hashtag_data.priority_tag, "p2")

	def test_status_tags(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.scheduled_tag = None
		hashtag_data.status_tag = None
		hashtag_data.priority_tag = None
		hashtag_data.other_hashtags = ["#o", "#x"]

		hashtag_data.copy_tags_from_other_hashtags()
		self.assertEqual(hashtag_data.status_tag, "o")


@patch("hashtag_data.SCHEDULED_TAG", "s")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
class StrikeThroughScheduledTagTest(TestCase):
	def test_add_strikethrough_entity(self, *args):
		hashtag_data = HashtagData()
		scheduled_tag = "#s 2024-01-23 13:00"
		text = f"text\n#o #cc #p {scheduled_tag}"
		hashtag_data.hashtag_indexes = [3, 0, [1], 2]
		entities = test_helper.create_hashtag_entity_list(text)
		entities[-1].length = len(scheduled_tag)
		entities = hashtag_data.strike_through_scheduled_tag(text, entities)

		strikethrough_entity = entities[-1]

		self.assertEqual(strikethrough_entity.type, "strikethrough")
		self.assertEqual(strikethrough_entity.aligned_to_utf8, True)
		self.assertEqual(strikethrough_entity.length, 16)
		self.assertEqual(strikethrough_entity.offset, 18)

	def test_add_strikethrough_entity_with_other_tags(self, *args):
		hashtag_data = HashtagData()
		scheduled_tag = "#s 2024-01-23 13:00"
		text = f"text\n#o #cc #p {scheduled_tag} #test #asdf"
		hashtag_data.hashtag_indexes = [3, 0, [1], 2]
		entities = test_helper.create_hashtag_entity_list(text)
		entities[3].length = len(scheduled_tag)
		entities = hashtag_data.strike_through_scheduled_tag(text, entities)

		strikethrough_entity = None
		for i, entity in enumerate(entities):
			if i == 0:
				continue
			previous_entity = entities[i - 1]
			self.assertTrue(previous_entity.offset <= entity.offset)

			if entity.type == "strikethrough":
				strikethrough_entity = entity

		self.assertEqual(strikethrough_entity.type, "strikethrough")
		self.assertEqual(strikethrough_entity.aligned_to_utf8, True)
		self.assertEqual(strikethrough_entity.length, 16)
		self.assertEqual(strikethrough_entity.offset, 18)


@patch("hashtag_data.SCHEDULED_TAG", "x")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
class StrikeThroughTicketNumberTest(TestCase):
	def test_add_strikethrough_entity(self, *args):
		hashtag_data = HashtagData()
		text = f"123. text\n#o #cc #p"
		hashtag_data.post_data = test_helper.create_mock_message(text, [])
		hashtag_data.post_data.message_id = 123

		entities = [
			telebot.types.MessageEntity(type="text_link", offset=0, length=3, url="https://t.me/c/1234567890/123"),
		] + test_helper.create_hashtag_entity_list(text)
		entities = hashtag_data.strike_through_ticket_number(text, entities)

		first_entity = entities[0]

		self.assertEqual(first_entity.type, "strikethrough")
		self.assertEqual(first_entity.aligned_to_utf8, True)
		self.assertEqual(first_entity.length, 3)
		self.assertEqual(first_entity.offset, 0)


@patch("hashtag_data.SCHEDULED_TAG", "s")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("hashtag_data.HashtagData.get_entities_to_ignore", return_value=range(0, 0))
class RemoveStrikethroughEntitiesTest(TestCase):
	def test_remove_scheduled_date_strikethrough_entity(self, *args):
		hashtag_data = HashtagData()
		scheduled_tag = "#s 2024-01-23 13:00"
		text = f"text\n#o #cc #p " + scheduled_tag

		entities = test_helper.create_hashtag_entity_list(text)
		entities[-1].length = len(scheduled_tag)
		entities.append(telebot.types.MessageEntity(type="strikethrough", offset=18, length=16))

		hashtag_data.post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data.message_id = 123

		hashtag_data.remove_strikethrough_entities()

		result_entities = hashtag_data.post_data.entities
		is_strikethrough_entity_exists = any([e.type == "strikethrough" for e in result_entities])
		self.assertFalse(is_strikethrough_entity_exists)
		self.assertEqual(len(result_entities), 4)

	@patch("hashtag_data.HashtagData.get_entities_to_ignore", return_value=range(0,0))
	def test_remove_incomplete_scheduled_date_strikethrough_entity(self, *args):
		hashtag_data = HashtagData()
		scheduled_tag = "#s 2024-01-23 12:"
		text = f"text\n#o #cc #p " + scheduled_tag

		entities = test_helper.create_hashtag_entity_list(text)
		entities[-1].length = len(scheduled_tag)
		entities.append(telebot.types.MessageEntity(type="strikethrough", offset=18, length=len(scheduled_tag) - 3))

		hashtag_data.post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data.message_id = 123

		hashtag_data.remove_strikethrough_entities()

		result_entities = hashtag_data.post_data.entities
		is_strikethrough_entity_exists = any([e.type == "strikethrough" for e in result_entities])
		self.assertFalse(is_strikethrough_entity_exists)
		self.assertEqual(len(result_entities), 4)

	@patch("hashtag_data.HashtagData.get_entities_to_ignore", return_value=range(2,2))
	def test_remove_ticket_number_strikethrough_entity(self, *args):
		hashtag_data = HashtagData()
		text = f"123. text\n#o #cc #p"
		hashtag_data.post_data = test_helper.create_mock_message(text, [])
		hashtag_data.post_data.message_id = 123

		first_strikethrough_entities = [
			telebot.types.MessageEntity(type="strikethrough", offset=0, length=3),
			telebot.types.MessageEntity(type="text_link", offset=0, length=3, url="https://t.me/c/1234567890/123"),
		] + test_helper.create_hashtag_entity_list(text)

		first_link_entities = [
			telebot.types.MessageEntity(type="text_link", offset=0, length=3, url="https://t.me/c/1234567890/123"),
			telebot.types.MessageEntity(type="strikethrough", offset=0, length=3),
		] + test_helper.create_hashtag_entity_list(text)

		for entities in [first_link_entities, first_strikethrough_entities]:
			hashtag_data.post_data.entities = entities
			hashtag_data.remove_strikethrough_entities()

			result_entities = hashtag_data.post_data.entities
			is_strikethrough_entity_exists = any([e.type == "strikethrough" for e in result_entities])
			self.assertFalse(is_strikethrough_entity_exists)
			self.assertEqual(len(result_entities), 4)


@patch("hashtag_data.SCHEDULED_TAG", "s")
@patch("hashtag_data.HashtagData.__init__", return_value=None)
class FindScheduledTagInOtherHashtagsTest(TestCase):
	def test_find_scheduled_tag(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.other_hashtags = ["#ab", "#bb", "#test", "#s 2024-01-23 13:00"]

		result = hashtag_data.find_scheduled_tag_in_other_hashtags()
		self.assertEqual(result, "2024-01-23 13:00")

	def test_multiple_scheduled_tags(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.other_hashtags = ["#ab", "#bb", "#s 2024-01-23 13:00", "#s 2024-03-01 12:00", "#s 2024-08-10 22:30"]

		result = hashtag_data.find_scheduled_tag_in_other_hashtags()
		self.assertEqual(result, "2024-01-23 13:00")

	def test_scheduled_tag_without_time(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.other_hashtags = ["#ab", "#bb", "#s 2024-03-01", "#s 2024-03-01 12:00"]

		result = hashtag_data.find_scheduled_tag_in_other_hashtags()
		self.assertEqual(result, "2024-03-01 00:00")


@patch("hashtag_data.HashtagData.__init__", return_value=None)
class UpdateScheduledStatusTest(TestCase):
	@patch("time.time", return_value=1717189200)  # 2024-06-01
	@patch("hashtag_data.HashtagData.is_scheduled", return_value=True)
	@patch("hashtag_data.HashtagData.get_scheduled_datetime_str", return_value="2024-03-01 12:00")
	def test_after_sent_date(self, *args):
		hashtag_data = HashtagData()

		hashtag_data.update_scheduled_status()
		self.assertTrue(hashtag_data.is_sent)

	@patch("time.time", return_value=1717189200)  # 2024-06-01
	@patch("hashtag_data.HashtagData.is_scheduled", return_value=True)
	@patch("hashtag_data.HashtagData.get_scheduled_datetime_str", return_value="2024-09-01 12:00")
	def test_before_sent_date(self, *args):
		hashtag_data = HashtagData()

		hashtag_data.update_scheduled_status()
		self.assertFalse(hashtag_data.is_sent)

	@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
	def test_not_scheduled(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.is_sent = None

		hashtag_data.update_scheduled_status()
		self.assertFalse(hashtag_data.is_sent)

	@patch("hashtag_data.HashtagData.is_scheduled", return_value=True)
	@patch("hashtag_data.HashtagData.get_scheduled_datetime_str", return_value="2222-22-22 22:22")
	@patch("hashtag_data.HashtagData.is_scheduled", return_value=False)
	def test_invalid_datetime(self, *args):
		hashtag_data = HashtagData()
		hashtag_data.is_sent = None

		hashtag_data.update_scheduled_status()
		self.assertFalse(hashtag_data.is_sent)


@patch("config_utils.HASHTAGS_BEFORE_UPDATE", {"CLOSED": "old_c", "OPENED": "old_o", "PRIORITY": "old_p", "SCHEDULED": "old_sch"})
@patch("hashtag_data.OPENED_TAG", "opened")
@patch("hashtag_data.CLOSED_TAG", "closed")
@patch("hashtag_data.SCHEDULED_TAG", "sch")
@patch("hashtag_data.PRIORITY_TAG", "priority")
class OldTagReplacementTest(TestCase):
	def test_replace_old_status_tag(self, *args):
		text = "test\n#old_o #ab #priority1"
		entities = test_helper.create_hashtag_entity_list(text)

		updated_text, updated_entities = HashtagData.replace_old_status_tag(text, entities, 0)
		self.assertEqual(updated_text, "test\n#opened #ab #priority1")
		self.assertEqual(updated_entities[0].length, 7)

	def test_replace_old_scheduled_tag(self, *args):
		scheduled_tag = "#old_sch 2024-05-01 19:00"
		text = f"test\n#opened #ab #priority1 {scheduled_tag}"
		entities = test_helper.create_hashtag_entity_list(text)
		entities[3].length = len(scheduled_tag)

		updated_text, updated_entities = HashtagData.replace_old_scheduled_tag(text, entities, 3)
		self.assertEqual(updated_text, "test\n#opened #ab #priority1 #sch 2024-05-01 19:00")
		self.assertEqual(updated_entities[3].length, 21)

	def test_replace_old_priority_tag(self, *args):
		text = f"test\n#opened #ab #old_p1"
		entities = test_helper.create_hashtag_entity_list(text)

		priority_tag_index = 2
		updated_text, updated_entities = HashtagData.replace_old_priority_tag(text, entities, priority_tag_index)
		self.assertEqual(updated_text, "test\n#opened #ab #priority1")
		self.assertEqual(updated_entities[priority_tag_index].length, 10)


	def test_tags_to_replace_not_found(self, *args):
		scheduled_tag = "#sch 2024-05-01 19:00"
		text = f"test\n#opened #ab #priority1 {scheduled_tag}"
		entities = test_helper.create_hashtag_entity_list(text)

		for i in range(len(entities)):
			text, entities = HashtagData.replace_old_status_tag(text, entities, i)
			text, entities = HashtagData.replace_old_scheduled_tag(text, entities, i)
			text, entities = HashtagData.replace_old_priority_tag(text, entities, i)

		self.assertEqual(text, "test\n#opened #ab #priority1 #sch 2024-05-01 19:00")


class OldTagCheckTest(TestCase):
	@patch("config_utils.HASHTAGS_BEFORE_UPDATE", None)
	def test_without_updated_hashtags(self, *args):
		self.assertFalse(HashtagData.check_old_status_tag("test"))
		self.assertFalse(HashtagData.check_old_scheduled_tag("test"))
		self.assertFalse(HashtagData.check_old_priority_tag("test"))

	@patch("config_utils.HASHTAGS_BEFORE_UPDATE", {"TEST": "tag"})
	def test_missing_hashtag_values(self, *args):
		self.assertFalse(HashtagData.check_old_status_tag("test"))
		self.assertFalse(HashtagData.check_old_scheduled_tag("test"))
		self.assertFalse(HashtagData.check_old_priority_tag("test"))

	@patch("config_utils.HASHTAGS_BEFORE_UPDATE", {"CLOSED": "old_c", "OPENED": "old_o", "PRIORITY": "old_p", "SCHEDULED": "old_sch"})
	def test_hashtag_check(self, *args):
		self.assertTrue(HashtagData.check_old_status_tag("old_o"))
		self.assertTrue(HashtagData.check_old_status_tag("old_c"))
		self.assertTrue(HashtagData.check_old_scheduled_tag("old_sch"))
		self.assertTrue(HashtagData.check_old_priority_tag("old_p"))


@patch("hashtag_data.HashtagData.__init__", return_value=None)
class CheckLastLineTest(TestCase):
	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	@patch("utils.get_post_content")
	def test_last_line_with_text(self, mock_get_post_content, *args):
		text = "text\n #open #bb #p2 test"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		hashtag_data = HashtagData()
		hashtag_data.post_data = test_helper.create_mock_message(text, [])
		result = hashtag_data.check_last_line()
		self.assertFalse(result)

	@patch("hashtag_data.HashtagData.is_service_tag", return_value=True)
	@patch("utils.get_post_content")
	def test_with_service_hashtags(self, mock_get_post_content, *args):
		text = "text\n #open #bb #p2"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		hashtag_data = HashtagData()
		hashtag_data.post_data = test_helper.create_mock_message(text, [])
		result = hashtag_data.check_last_line()
		self.assertTrue(result)

	@patch("hashtag_data.HashtagData.is_service_tag", return_value=False)
	@patch("utils.get_post_content")
	def test_no_service_hashtags(self, mock_get_post_content, *args):
		text = "text\n #test #asdf"
		entities = test_helper.create_hashtag_entity_list(text)
		mock_get_post_content.return_value = (text, entities)

		hashtag_data = HashtagData()
		hashtag_data.post_data = test_helper.create_mock_message(text, [])
		result = hashtag_data.check_last_line()
		self.assertFalse(result)


@patch("hashtag_data.HashtagData.__init__", return_value=None)
class InsertDefaultTagsTest(TestCase):
	def setUp(self):
		hashtag_data_module.OPENED_TAG = "open"
		hashtag_data_module.CLOSED_TAG = "closed"
		hashtag_data_module.PRIORITY_TAG = "p"
		hashtag_data_module.SCHEDULED_TAG = "sch"

	@patch("hashtag_data.HashtagData.is_status_missing", return_value=True)
	def test_missing_status_tag(self, *args):
		hashtag_data_module.DEFAULT_USER_DATA = {}
		hashtag_data = HashtagData()
		hashtag_data.main_channel_id = 12345678
		hashtag_data.insert_default_tags()
		self.assertEqual(hashtag_data.status_tag, "open")

	@patch("hashtag_data.HashtagData.is_status_missing", return_value=True)
	@patch("hashtag_data.HashtagData.insert_default_user")
	@patch("hashtag_data.HashtagData.insert_default_priority")
	def test_insert_user_and_priority(self, mock_insert_default_priority, mock_insert_default_user, *args):
		main_channel_id = 12345678
		hashtag_data_module.DEFAULT_USER_DATA = {"12345678": "ab 1"}
		hashtag_data = HashtagData()
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.user_tags = []
		hashtag_data.insert_default_tags()
		mock_insert_default_priority.assert_called_once()
		mock_insert_default_user.assert_called_once()


@patch("hashtag_data.HashtagData.__init__", return_value=None)
class ExtractScheduledTagFromTextTest(TestCase):
	def test_invalid_minutes(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 14:77"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 14:00")

	def test_invalid_hours(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 26:77"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 00:00")

	def test_normal_scheduled_tag(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 14:30"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16 14:30"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 14:30")

	def test_without_time(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 asdf"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 00:00")

	def test_incorrect_tag(self, *args):
		hashtag_data = HashtagData()
		text = "#s test text"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s")

	def test_time_without_zeros_invalid_minute(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 2:82"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 02:00")

	def test_time_without_zeros(self, *args):
		hashtag_data = HashtagData()
		text = "#s 2024-05-16 2:5"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16 2:2"))
		result = hashtag_data.extract_scheduled_tag_from_text(text, entity)
		self.assertEqual(result, "s 2024-05-16 02:05")

@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("hashtag_data.SCHEDULED_TAG", "s")
@patch("config_utils.USER_TAGS", {"aa": 1, "bb": 2, "cc": 3, "dd": 4, "ff": 5})
@patch("config_utils.DEFAULT_USER_DATA", {"123": "ff 2"})
@patch("user_utils.get_member_ids_channel", return_value=[1, 2, 4, 5])
@patch("db_utils.get_assigned_users_by_channel", return_value=[(10, "ff"), (8, "bb"), (3, "dd")])
class ExtractHashtagsTest(TestCase):
	def test_time_without_zeros(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		hashtag_data.is_hashtag_line_present = False
		text = "#s 2024-05-16 2:5"
		entity = telebot.types.MessageEntity(type="hashtag", offset=0, length=len("#s 2024-05-16 2:2"))
		post_data = test_helper.create_mock_message(text, [entity])
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, False)
		mock_get_assigned_users_by_channel.assert_not_called()
		self.assertEqual(result, ("s 2024-05-16 02:05", None, [], None))
		self.assertEqual(hashtag_data.comment, None)

	def test_user_tags(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#aa #bb #cc #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, False)
		mock_get_assigned_users_by_channel.assert_not_called()
		self.assertEqual(result, (None, None, ["aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.comment, None)

	def test_user_tags_invalid_assigned(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#cc #aa #bb #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, False)
		mock_get_assigned_users_by_channel.assert_not_called()
		self.assertEqual(result, (None, None, ["aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.comment, None)

	def test_user_tags_invalid_assigned_with_default(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#cc #aa #bb #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, True)
		mock_get_assigned_users_by_channel.assert_not_called()
		self.assertEqual(result, (None, None, ["ff", "aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.hashtag_indexes, (None, None, [2,3,4], None))
		self.assertEqual(hashtag_data.comment, (f"The ticket was reassigned to user tag #ff as the previous user is not a workspace member.", None))

	def test_user_tags_invalid_assigned_and_default(self, mock_get_assigned_users_by_channel, mock_get_member_ids_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#cc #aa #bb #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		mock_get_member_ids_channel.return_value = [1, 2, 4]
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, True)
		mock_get_assigned_users_by_channel.assert_called_once_with(main_channel_id)
		self.assertEqual(result, (None, None, ["bb", "aa", "dd"], None))
		self.assertEqual(hashtag_data.hashtag_indexes, (None, None, [2,3,4], None))
		self.assertEqual(hashtag_data.comment, (f"The ticket was reassigned to user tag #bb as the previous user is not a workspace member.", None))

	def test_user_tags_invalid_assigned_with_empty_default(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 125
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#cc #aa #bb #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, True)
		mock_get_assigned_users_by_channel.assert_called_once_with(main_channel_id)
		self.assertEqual(result, (None, None, ["ff", "aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.hashtag_indexes, (None, None, [2,3,4], None))
		self.assertEqual(hashtag_data.comment, (f"The ticket was reassigned to user tag #ff as the previous user is not a workspace member.", None))

	def test_user_tags_invalid_assigned_with_empty_default_and_assigned(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 125
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#cc #aa #bb #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		mock_get_assigned_users_by_channel.return_value = []
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, True)
		mock_get_assigned_users_by_channel.assert_called_once_with(main_channel_id)
		self.assertEqual(result, (None, None, ["aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.hashtag_indexes, (None, None, [2,3,4], None))
		self.assertEqual(hashtag_data.comment, (f"The ticket was reassigned to user tag #aa as the previous user is not a workspace member.", None))

	def test_user_tags_with_default(self, mock_get_assigned_users_by_channel, *args):
		hashtag_data = HashtagData()
		hashtag_data.comment = None
		hashtag_data.is_hashtag_line_present = True
		main_channel_id = 123
		hashtag_data.main_channel_id = main_channel_id
		text = "\n#aa #bb #cc #dd"
		entities = [telebot.types.MessageEntity(type="hashtag", offset=0, length=1),
					telebot.types.MessageEntity(type="hashtag", offset=1, length=len("#aa")),
					telebot.types.MessageEntity(type="hashtag", offset=5, length=len("#cc")),
					telebot.types.MessageEntity(type="hashtag", offset=9, length=len("#bb")),
					telebot.types.MessageEntity(type="hashtag", offset=13, length=len("#dd")),
					]
		post_data = test_helper.create_mock_message(text, entities)
		hashtag_data.post_data = post_data
		result = hashtag_data.extract_hashtags(post_data, main_channel_id, True)
		mock_get_assigned_users_by_channel.assert_not_called()
		self.assertEqual(result, (None, None, ["aa", "bb", "dd"], None))
		self.assertEqual(hashtag_data.hashtag_indexes, (None, None, [1,2,4], None))
		self.assertEqual(hashtag_data.comment, None)


@patch("hashtag_data.HashtagData.__init__", return_value=None)
@patch("config_utils.USER_TAGS", {"AA": 123456, "CC": 654321, "NN": 123654})
@patch("user_utils.MEMBER_CACHE", {-10012345678: {"user_ids": [123456, 123654], "time": 1745924296}})
@patch("time.time", return_value=1745924296)
class CheckUserTagTest(TestCase):
	@patch("user_utils.get_member_ids_channels")
	def test_functions(self, mock_get_member_ids_channels, *args):
		hashtag_data = HashtagData()
		channel_id = -10012345678

		hashtag_data.check_user_tag("AA")
		mock_get_member_ids_channels.assert_not_called()
		hashtag_data.check_user_tag("AA", channel_id)
		mock_get_member_ids_channels.assert_called_once_with([-10012345678])

	def test_result(self, *args):
		hashtag_data = HashtagData()
		channel_id = -10012345678
		self.assertTrue(hashtag_data.check_user_tag("AA"))
		self.assertTrue(hashtag_data.check_user_tag("CC"))
		self.assertFalse(hashtag_data.check_user_tag("aa"))
		self.assertTrue(hashtag_data.check_user_tag("AA", channel_id))
		self.assertFalse(hashtag_data.check_user_tag("CC", channel_id))





if __name__ == "__main__":
	main()
