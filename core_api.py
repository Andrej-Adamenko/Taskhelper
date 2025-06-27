import asyncio
import functools
import logging
from math import floor
from typing import Union

import pyrogram
from pyrogram import Client, utils
from pyrogram.errors import FloodWait
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

def thread_error(func):
	async def inner_function(*args, **kwargs):
		try:
			return await func(*args, **kwargs)
		except FloodWait as E:
			logging.info(f"Wait {E.value} seconds")
			await asyncio.sleep(E.value)
			return await inner_function(*args, **kwargs)
		except Exception as E:
			logging.error(f"Core api {func.__name__}{args} exception - {E}")
		return None

	return inner_function


def thread_async_to_sync(func):
	def inner_function(*args, **kwargs):
		@thread_error
		@functools.wraps(func)
		async def inner_function_async(*args, **kwargs):
			if "client" not in kwargs:
				async with create_client() as client:
					kwargs["client"] = client
					return await func(*args, **kwargs)
			return await func(*args, **kwargs)
		return asyncio.run(inner_function_async(*args, **kwargs))
	return inner_function


@thread_async_to_sync
async def get_messages(chat_id: int, last_msg_id: int, limit: int, /, client: pyrogram.Client,
					   message_ids: list = None, stop_flag: dict = None) -> list | None:
	COUNT_FOR_SLEEP_MORE = 350
	if not message_ids:
		message_ids = list(range(1, last_msg_id + 1))
	read_counter = 0
	time_sleep: float = limit / 10 if len(message_ids) > (floor(COUNT_FOR_SLEEP_MORE / limit) * limit) else 1
	exported_messages= []

	while read_counter < len(message_ids):
		if stop_flag and "stop" in stop_flag and stop_flag["stop"]:
			logging.info(f"Stopping export progress, count exported: {read_counter}")
			return None

		try:
			exported_messages += await client.get_messages(chat_id, message_ids[read_counter:read_counter + limit])
		except FloodWait as E:
			logging.info(f"Wait {E.value} seconds")
			await asyncio.sleep(E.value)
			continue

		read_counter += limit
		logging.info(f"Exporting progress: {min(read_counter, len(message_ids))}/{len(message_ids)}")

		if read_counter < len(message_ids):
			await asyncio.sleep(time_sleep)

	return exported_messages


@thread_async_to_sync
async def get_members(chat_ids: list, /, client: pyrogram.Client) -> dict | None:
	users = {}

	for chat_id in chat_ids:
		members = await __get_members_for_chat(chat_id, client=client)
		users[chat_id] = members if members is not None else []
		await asyncio.sleep(0.5)

	return users


@thread_error
async def __get_members_for_chat(chat_id: int, /, client: pyrogram.Client) -> list | None:
	users = []

	async for member in client.get_chat_members(chat_id):
		users.append(member.user)

	return users


@thread_async_to_sync
async def get_user(identifier: Union[str, int], /, client: pyrogram.Client) -> User | None:
	return await client.get_users(identifier)

