PRIORITY_TAG = "п"
OPENED_TAG = "о"
CLOSED_TAG = "х"


def parse_hashtags(post_data):
    if not post_data.entities:
        return []

    hashtags = []

    for entity in post_data.entities:
        if entity.type != "hashtag":
            continue
        hashtag_name = post_data.text[entity.offset + 1:entity.offset + entity.length]
        hashtags.append(hashtag_name)

    return hashtags


def forward_to_subchannel(bot, post_data, subchannel_data, hashtags):
    if OPENED_TAG not in hashtags:
        return

    main_channel_id = post_data.chat.id
    message_id = post_data.message_id

    subchannel_id = get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags)
    if subchannel_id:
        bot.copy_message(chat_id=subchannel_id, message_id=post_data.message_id, from_chat_id=main_channel_id)


def get_subchannel_id_from_hashtags(main_channel_id, subchannel_data, hashtags):
    main_channel_id_str = str(main_channel_id)
    if main_channel_id_str not in subchannel_data:
        return

    priority = None
    user_priority_list = None

    subchannel_users = subchannel_data[main_channel_id_str]
    for user in subchannel_users:
        if user in hashtags:
            user_priority_list = subchannel_users[user]

    if not user_priority_list:
        return

    for hashtag in hashtags:
        if hashtag.startswith(PRIORITY_TAG) and len(hashtag) == 2:
            priority = hashtag[len(PRIORITY_TAG):]

    if priority not in user_priority_list:
        return

    return user_priority_list[priority]


def get_all_subchannel_ids(subchannel_data):
    subchannel_ids = []
    for main_channel_id in subchannel_data:
        channel_users = subchannel_data[main_channel_id]
        for user in channel_users:
            user_priorities = channel_users[user]
            for priority in user_priorities:
                subchannel_id = user_priorities[priority]
                subchannel_ids.append(subchannel_id)

    return subchannel_ids
