from unittest import TestCase, main
from unittest.mock import patch

import telebot.types

from hashtag_data import HashtagData
import test_helper


@patch("hashtag_data.PRIORITY_TAG", "p")
@patch("hashtag_data.OPENED_TAG", "o")
class FindCopyUsersFromText(TestCase):
	@patch("db_utils.is_user_tag_exists")
	@patch("hashtag_data.HashtagData.__init__")
	def test_find_mentioned_users(self, mock_hashtag_data_init, mock_is_user_tag_exists):
		mock_hashtag_data_init.return_value = None

		user_tags = ["aa", "bb", "cc"]
		is_user_tag = lambda channel_id, user_tag: user_tag in user_tags
		mock_is_user_tag_exists.side_effect = is_user_tag

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

	@patch("db_utils.is_user_tag_exists")
	@patch("hashtag_data.HashtagData.__init__")
	def test_no_mentioned_users(self, mock_hashtag_data_init, mock_is_user_tag_exists):
		mock_hashtag_data_init.return_value = None

		user_tags = ["cc"]
		is_user_tag = lambda channel_id, user_tag: user_tag in user_tags
		mock_is_user_tag_exists.side_effect = is_user_tag

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

	@patch("db_utils.is_user_tag_exists")
	@patch("hashtag_data.HashtagData.__init__")
	def test_assign_user(self, mock_hashtag_data_init, mock_is_user_tag_exists):
		mock_hashtag_data_init.return_value = None

		user_tags = ["aa", "bb"]
		is_user_tag = lambda channel_id, user_tag: user_tag in user_tags
		mock_is_user_tag_exists.side_effect = is_user_tag

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
		self.assertEqual(result, ["aa", "bb"])
		self.assertEqual(hashtag_data.user_tags, ["aa", "bb"])


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
		mock_is_service_tag.side_effect = lambda tag: tag in service_hashtags

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
		mock_is_service_tag.side_effect = lambda tag: tag in service_hashtags

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
		hashtag_data.hashtag_indexes = [None, None, [], 0]
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
		hashtag_data.hashtag_indexes = [None, None, [], 0]
		hashtag_data.is_hashtag_line_present = True
		result = hashtag_data.remove_redundant_priority_tags(text, entities)
		self.assertEqual(result[0], f"text\n#aa #bb #p1")


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


if __name__ == "__main__":
	main()
