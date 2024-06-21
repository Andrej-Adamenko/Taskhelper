from unittest import TestCase, main
from unittest.mock import patch

from hashtag_data import HashtagData, OPENED_TAG, PRIORITY_TAG
import test_utils


class FindMentionedUsersTest(TestCase):
	@patch("db_utils.is_user_tag_exists")
	@patch("hashtag_data.HashtagData.__init__")
	def test_find_mentioned_users(self, mock_hashtag_data_init, mock_is_user_tag_exists):
		mock_hashtag_data_init.return_value = None

		user_tags = ["aa", "bb", "cc"]
		is_user_tag = lambda channel_id, user_tag: user_tag in user_tags
		mock_is_user_tag_exists.side_effect = is_user_tag

		text = f"text #aa #bb\n#{OPENED_TAG} #cc #{PRIORITY_TAG} #user_tag"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.hashtag_indexes = [None, 2, [3], 4]
		hashtag_data.main_channel_id = main_channel_id
		result = hashtag_data.find_mentioned_users(post_data)
		self.assertEqual(result, ["aa", "bb"])

	@patch("db_utils.is_user_tag_exists")
	@patch("hashtag_data.HashtagData.__init__")
	def test_no_mentioned_users(self, mock_hashtag_data_init, mock_is_user_tag_exists):
		mock_hashtag_data_init.return_value = None

		user_tags = ["cc"]
		is_user_tag = lambda channel_id, user_tag: user_tag in user_tags
		mock_is_user_tag_exists.side_effect = is_user_tag

		text = f"text test\n#{OPENED_TAG} #cc #{PRIORITY_TAG} #user_tag"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)

		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		hashtag_data.hashtag_indexes = [None, 0, [1], 2]
		hashtag_data.main_channel_id = main_channel_id
		result = hashtag_data.find_mentioned_users(post_data)
		self.assertEqual(result, [])


class GetEntitiesToIgnoreTest(TestCase):
	@patch("hashtag_data.HashtagData.__init__")
	def test_middle_and_back_entities(self, mock_hashtag_data_init):
		mock_hashtag_data_init.return_value = None

		text = f"text #aa #bb\n#{OPENED_TAG} #cc #{PRIORITY_TAG} #user_tag"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(0, 2))

	@patch("hashtag_data.HashtagData.__init__")
	def test_front_entities(self, mock_hashtag_data_init):
		mock_hashtag_data_init.return_value = None

		text = f"#aa #bb test #cc test"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(2, 3))

	@patch("hashtag_data.HashtagData.__init__")
	def test_back_entities(self, mock_hashtag_data_init):
		mock_hashtag_data_init.return_value = None

		text = f"test text\n#{OPENED_TAG} #cc #{PRIORITY_TAG} #user_tag"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(0, 0))

	@patch("hashtag_data.HashtagData.__init__")
	def test_middle_and_front_entities(self, mock_hashtag_data_init):
		mock_hashtag_data_init.return_value = None

		text = f"#{OPENED_TAG} #cc #{PRIORITY_TAG} test #aa #bb text"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(3, 5))

	@patch("hashtag_data.HashtagData.__init__")
	def test_end_of_line_entities(self, mock_hashtag_data_init):
		mock_hashtag_data_init.return_value = None

		text = f"#aa text #bb #user_tag"
		entities = test_utils.create_hashtag_entity_list(text)
		post_data = test_utils.create_mock_message(text, entities)
		main_channel_id = 123

		hashtag_data = HashtagData(post_data, main_channel_id)
		result = hashtag_data.get_entities_to_ignore(text, entities)
		self.assertEqual(result, range(1, 3))


if __name__ == "__main__":
	main()
