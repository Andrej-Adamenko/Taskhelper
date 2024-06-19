from unittest import TestCase, main
from unittest.mock import Mock, patch

from telebot.types import Message, MessageEntity

from hashtag_utils import insert_hashtag_in_post, insert_hashtags


class InsertHashtagInPostTest(TestCase):
	@patch("hashtag_utils.MessageEntity")
	def test_no_position(self, MockMessageEntity):
		mock_message = MockMessageEntity.return_value
		text = "text"
		hashtag = "hashtag"

		result = insert_hashtag_in_post(text, [], hashtag)

		MockMessageEntity.assert_called_once_with(
			type="hashtag", offset=len(text) + 1, length=len(hashtag))
		self.assertEqual(result[0], f"{text} {hashtag}")
		self.assertEqual(result[1], [mock_message])

	@patch("hashtag_utils.MessageEntity")
	def test_with_additional_space(self, MockMessageEntity):
		mock_message = MockMessageEntity.return_value
		text = "test text"
		hashtag = "#hashtag"
		position = 5

		result = insert_hashtag_in_post(text, [], hashtag, position)

		MockMessageEntity.assert_called_once_with(
			type="hashtag", offset=position, length=len(hashtag))
		self.assertEqual(result[0], "test #hashtag text")
		self.assertEqual(result[1], [mock_message])

	@patch("hashtag_utils.MessageEntity")
	def test_without_additional_space(self, MockMessageEntity):
		mock_message = MockMessageEntity.return_value
		text = "test\n text"
		hashtag = "#hashtag"
		position = 5

		result = insert_hashtag_in_post(text, [], hashtag, position)

		MockMessageEntity.assert_called_once_with(
			type="hashtag", offset=position, length=len(hashtag))
		self.assertEqual(result[0], "test\n#hashtag text")
		self.assertEqual(result[1], [mock_message])


class InsertHashtagsTest(TestCase):
	@patch("utils.get_post_content")
	@patch("hashtag_utils.insert_hashtag_in_post")
	@patch("utils.set_post_content")
	def test_no_entities(self, mock_set_post_content, mock_insert_hashtag_in_post, mock_get_post_content):
		text = "text"
		entities = None
		mock_get_post_content.return_value = (text, entities)

		new_text = Mock()
		new_entities = Mock()
		mock_insert_hashtag_in_post.return_value = (new_text, new_entities)

		mock_message = Mock(spec=Message)
		tag = "tag"
		result = insert_hashtags(mock_message, [tag])

		mock_get_post_content.assert_called_once_with(mock_message)
		mock_insert_hashtag_in_post.assert_called_once_with(
			text + "\n", entities, f"#{tag}")
		mock_set_post_content.assert_called_once_with(
			mock_message, new_text, new_entities)
		self.assertEqual(result, mock_message)

	@patch("utils.get_post_content")
	@patch("utils.set_post_content")
	def test_last_line_hashtags(self, mock_set_post_content, mock_get_post_content):
		text = "text\n#hashtag"
		entities = [MessageEntity(type="hashtag", offset=5, length=8)]
		mock_get_post_content.return_value = (text, entities)

		mock_message = Mock(spec=Message)
		tag = "test"
		result = insert_hashtags(mock_message, [tag])

		mock_set_post_content.assert_called_once_with(
			mock_message, "text\n#test #hashtag", entities)
		self.assertEqual(result, mock_message)


if __name__ == "__main__":
	main()
