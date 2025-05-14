import asyncio
import logging
import time
from typing import Union, Any, Coroutine

import pyrogram
from pyrogram import Client, utils, enums
from pyrogram.types import User

from config_utils import BOT_TOKEN, APP_API_ID, APP_API_HASH

'''
This is a fix for get_peer_type in Pyrogram module.
Original function throws an exception if channel id is less than -1002147483647.
This fix should be removed after this bug is fixed in Pyrogram module.
Issue with this bug: https://github.com/pyrogram/pyrogram/issues/1314
'''
def get_peer_type_fixed(peer_id: int) -> str:
	if peer_id < 0:
		if -999999999999 <= peer_id:
			return "chat"
		if -1997852516352 <= peer_id < -1000000000000:
			return "channel"
	elif 0 < peer_id <= 0xffffffffff:
		return "user"

	raise ValueError(f"Peer id invalid: {peer_id}")

# replace original function with fixed version
utils.get_peer_type = get_peer_type_fixed

def create_client() -> pyrogram.Client:
	return Client(
		"pyrogram_bot",
		api_id=APP_API_ID, api_hash=APP_API_HASH,
		bot_token=BOT_TOKEN
	)


def async_to_sync(func):
	def inner_function(*args, **kwargs):
		async def inner_function_ajax(*args, **kwargs):
			if "client" not in kwargs:
				async with create_client() as client:
					kwargs["client"] = client
					return await func(*args, **kwargs)
			return await func(*args, **kwargs)

		return asyncio.run(inner_function_ajax(*args, **kwargs))
	return inner_function


@async_to_sync
async def get_messages(chat_id: int, last_msg_id: int, limit: int, time_sleep: int, /, client: pyrogram.Client) -> list:
	message_ids = list(range(1, last_msg_id + 1))
	read_counter = 0
	exported_messages= []

	while read_counter < len(message_ids):
		exported_messages += await client.get_messages(chat_id, message_ids[read_counter:read_counter + limit])
		read_counter += limit
		logging.info(f"Exporting progress: {min(read_counter, len(message_ids))}/{len(message_ids)}")

		if read_counter < len(message_ids):
			await asyncio.sleep(time_sleep)

	return exported_messages


@async_to_sync
async def get_members(chat_ids: list, /, client: pyrogram.Client) -> dict:
	users = {}

	for chat_id in chat_ids:
		users[chat_id] = []
		async for member in client.get_chat_members(chat_id):
			users[chat_id].append(member.user)

	return users

@async_to_sync
async def get_user(identifier: Union[str, int], /, client: pyrogram.Client) -> User | None:
	try:
		return await client.get_users(identifier)
	except Exception as E:
		logging.info(f"Core api get_user({identifier}) exception: {E}")

	return None

