from unittest import TestCase, main
from unittest.mock import Mock
from telebot.types import MessageEntity, Message

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


if __name__ == "__main__":
	main()
