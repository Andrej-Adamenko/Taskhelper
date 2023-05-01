import logging
import sqlite3
import threading

DB_FILENAME = "taskhelper_data.db"

DB_CONNECTION = sqlite3.connect(DB_FILENAME, check_same_thread=False)
CURSOR = DB_CONNECTION.cursor()

DB_LOCK = threading.RLock()


def db_thread_lock(func):
	def inner_function(*args, **kwargs):
		try:
			DB_LOCK.acquire(True)
			return func(*args, **kwargs)
		except sqlite3.Error as E:
			logging.error(f"SQLite error in {func.__name__} function, error: {E.args}")
		finally:
			DB_LOCK.release()
	return inner_function


def initialize_db():
	create_tables()


def is_table_exists(table_name):
	sql = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name=(?)"
	CURSOR.execute(sql, (table_name,))
	result = CURSOR.fetchone()[0]
	return bool(result)


def create_tables():
	if not is_table_exists("discussion_messages"):
		discussion_messages_table_sql = '''
			CREATE TABLE "discussion_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"discussion_message_id"	INT NOT NULL
			); '''

		CURSOR.execute(discussion_messages_table_sql)

	if not is_table_exists("copied_messages"):
		copied_messages_table_sql = '''
			CREATE TABLE "copied_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"copied_message_id"	INT NOT NULL,
				"copied_channel_id"	INT NOT NULL
			); '''

		CURSOR.execute(copied_messages_table_sql)

	if not is_table_exists("last_message_ids"):
		last_message_ids_table_sql = '''
			CREATE TABLE "last_message_ids" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"chat_id"	INT NOT NULL,
				"last_message_id"	INT NOT NULL
			); '''

		CURSOR.execute(last_message_ids_table_sql)

	if not is_table_exists("comment_messages"):
		comment_messages_table_sql = '''
			CREATE TABLE "comment_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"discussion_chat_id"	INT NOT NULL,
				"message_id"	INT NOT NULL,
				"reply_to_message_id"	INT NOT NULL,
				"sender_id"	INT NOT NULL
			); '''

		CURSOR.execute(comment_messages_table_sql)

	if not is_table_exists("scheduled_messages"):
		scheduled_messages_table_sql = '''
			CREATE TABLE "scheduled_messages" (
				"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
				"main_message_id"	INT NOT NULL,
				"main_channel_id"	INT NOT NULL,
				"scheduled_message_id"	INT NOT NULL,
				"scheduled_channel_id"	INT NOT NULL,
				"send_time"	INT NOT NULL
			); '''

		CURSOR.execute(scheduled_messages_table_sql)


	DB_CONNECTION.commit()


@db_thread_lock
def insert_or_update_discussion_message(main_message_id, main_channel_id, discussion_message_id):
	if get_discussion_message_id(main_message_id, main_channel_id):
		sql = "UPDATE discussion_messages SET discussion_message_id=(?) WHERE main_message_id=(?) and main_channel_id=(?)"
	else:
		sql = "INSERT INTO discussion_messages (discussion_message_id, main_message_id, main_channel_id) VALUES (?, ?, ?)"

	CURSOR.execute(sql, (discussion_message_id, main_message_id, main_channel_id, ))
	DB_CONNECTION.commit()


@db_thread_lock
def get_discussion_message_id(main_message_id, main_channel_id):
	sql = "SELECT discussion_message_id FROM discussion_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def get_main_from_discussion_message(discussion_message_id, main_channel_id):
	sql = "SELECT main_message_id FROM discussion_messages WHERE discussion_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (discussion_message_id, main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def insert_copied_message(main_message_id, main_channel_id, copied_message_id, copied_channel_id):
	sql = "INSERT INTO copied_messages (copied_message_id, copied_channel_id, main_message_id, main_channel_id) VALUES (?, ?, ?, ?)"
	CURSOR.execute(sql, (copied_message_id, copied_channel_id, main_message_id, main_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def delete_copied_message(copied_message_id, copied_channel_id):
	sql = "DELETE FROM copied_messages WHERE copied_message_id=(?) and copied_channel_id=(?)"
	CURSOR.execute(sql, (copied_message_id, copied_channel_id))
	DB_CONNECTION.commit()


@db_thread_lock
def get_copied_message_data(main_message_id, main_channel_id):
	sql = "SELECT copied_message_id, copied_channel_id FROM copied_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchall()
	return result


@db_thread_lock
def insert_or_update_last_msg_id(last_message_id, chat_id):
	if get_last_message_id(chat_id):
		sql = "UPDATE last_message_ids SET last_message_id=(?) WHERE chat_id=(?)"
	else:
		sql = "INSERT INTO last_message_ids (last_message_id, chat_id) VALUES (?, ?)"

	CURSOR.execute(sql, (last_message_id, chat_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_last_message_id(chat_id):
	sql = "SELECT last_message_id FROM last_message_ids WHERE chat_id=(?)"
	CURSOR.execute(sql, (chat_id,))
	result = CURSOR.fetchone()
	if result:
		return result[0]


@db_thread_lock
def insert_comment_message(reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id):
	if is_comment_exist(discussion_message_id, discussion_chat_id):
		return

	sql = "INSERT INTO comment_messages (reply_to_message_id, message_id, discussion_chat_id, sender_id) VALUES (?, ?, ?, ?)"
	CURSOR.execute(sql, (reply_to_message_id, discussion_message_id, discussion_chat_id, sender_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def is_comment_exist(discussion_message_id, discussion_chat_id):
	sql = "SELECT id FROM comment_messages WHERE message_id=(?) and discussion_chat_id=(?)"
	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id,))
	result = CURSOR.fetchone()
	return bool(result)


@db_thread_lock
def get_comments_count(discussion_message_id, discussion_chat_id, ignored_sender_id=0):
	sql = '''
		WITH RECURSIVE
		  reply_messages(comment_id) AS (
			 SELECT (?)
			 UNION ALL
			 SELECT message_id FROM comment_messages, reply_messages WHERE reply_to_message_id = reply_messages.comment_id
			 AND discussion_chat_id = (?) AND sender_id != (?)
		  )
		SELECT count(comment_id) - 1 FROM reply_messages;
	'''

	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id, ignored_sender_id,))
	result = CURSOR.fetchone()
	return result[0]


@db_thread_lock
def get_comment_top_parent(discussion_message_id, discussion_chat_id):
	sql = '''
		WITH RECURSIVE
		  reply_messages(comment_id) AS (
		   SELECT (?)
		   UNION ALL
		   SELECT reply_to_message_id FROM comment_messages, reply_messages WHERE message_id = reply_messages.comment_id
		   AND discussion_chat_id = (?)
		  )
		SELECT MIN(comment_id) FROM reply_messages;	
	'''

	CURSOR.execute(sql, (discussion_message_id, discussion_chat_id,))
	result = CURSOR.fetchone()
	return result[0]


@db_thread_lock
def insert_scheduled_message(main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time):
	sql = "INSERT INTO scheduled_messages (main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time) VALUES (?, ?, ?, ?, ?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time,))
	DB_CONNECTION.commit()


@db_thread_lock
def update_scheduled_message(scheduled_message_id, scheduled_channel_id, send_time):
	sql = "UPDATE scheduled_messages SET send_time=(?) WHERE scheduled_message_id=(?) and scheduled_channel_id=(?)"
	CURSOR.execute(sql, (send_time, scheduled_message_id, scheduled_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_scheduled_message(main_message_id, main_channel_id):
	sql = "SELECT scheduled_message_id, scheduled_channel_id, send_time FROM scheduled_messages WHERE main_message_id=(?) and main_channel_id=(?)"
	CURSOR.execute(sql, (main_message_id, main_channel_id,))
	result = CURSOR.fetchone()
	if result:
		return result


@db_thread_lock
def delete_scheduled_message(scheduled_message_id, scheduled_channel_id):
	sql = "DELETE FROM scheduled_messages WHERE scheduled_message_id=(?) AND scheduled_channel_id=(?)"
	CURSOR.execute(sql, (scheduled_message_id, scheduled_channel_id,))
	DB_CONNECTION.commit()


@db_thread_lock
def get_all_scheduled_messages():
	sql = "SELECT main_message_id, main_channel_id, scheduled_message_id, scheduled_channel_id, send_time FROM scheduled_messages"
	CURSOR.execute(sql, ())
	result = CURSOR.fetchall()
	return result
