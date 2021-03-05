import re

from django.conf import settings

from slugify import slugify
from slackclient import SlackClient
import logging
logger = logging.getLogger(__name__)


slack_token = settings.SLACK_TOKEN
slack_client = SlackClient(slack_token)


class SlackError(Exception):
    pass


def channel_reference(channel_id):
    if channel_id is None:
        return None
    return f"<#{channel_id}>"


def user_reference(user_id):
    return f"<@{user_id}>"


def reference_to_id(value):
    """take a string containing <@U123ABCD> refs and extract first match"""
    m = re.search(r"<@(U[A-Z0-9]+)>", value)
    return m.group(1) if m else None


def get_channel_id(channel_name, auto_unarchive=False):
    logger.info(f"Getting channel ID for {channel_name}")
    logger.error(f"Getting channel ID for {channel_name}")
    logger.error("get_channel_id")
    logger.error(channel_name)
    print("get_channel_id")
    print(channel_name)
    next_cursor = None
    while next_cursor != "":
        response = slack_client.api_call(
            "conversations.list",
            exclude_archived=not auto_unarchive,
            exclude_members=True,
            limit=800,
            cursor=next_cursor,
        )

        # see if there's a next_cursor
        try:
            next_cursor = response["response_metadata"]["next_cursor"]
            logger.info(f"get_channel_id - next_cursor == [{next_cursor}]")
        except LookupError:
            logger.error(
                "get_channel_id - I guess checking next_cursor in response object didn't work."
            )

        for channel in response["channels"]:
            if channel["name"] == channel_name:
                if channel["is_archived"] and auto_unarchive:
                    unarchive_channel(channel["id"])
                logger.error(channel["id"])
                return channel["id"]

    raise SlackError(f"Channel '{name}' not found")
    # response = slack_client.api_call(
    #     "conversations.list",
    #     exclude_archived=False,
    #     exclude_members=True,
    #     limit=1000
    # )
    # logger.error(response)
    # print(response)
    # if not response.get("ok", False):
    #     raise SlackError(f"Failed to list channels : {response['error']}")
    #
    # for channel in response['channels']:
    #     if channel['name'] == channel_name:
    #         if channel['is_archived'] and auto_unarchive:
    #             unarchive_channel(channel['id'])
    #
    #         return channel['id']
    #
    # raise SlackError(f"Couldn't find id for channel {channel_name}")


def create_channel(channel_name):
    logger.error("create_channel")
    response = slack_client.api_call(
        "conversations.create",
        name=channel_name,
    )
    logger.error(response)
    if not response.get("ok", False):
        if response['error'] == 'name_taken':
            logger.error("name taken")
            raise SlackError(f"Channel already taken {channel_name} : {response['error']}")
        else:
            logger.error("other error")
    #raise SlackError(f"Response {response}")

    return response['channel']['id']

def set_channel_topic(channel_id, channel_topic):
    response = slack_client.api_call(
        "conversations.setTopic",
        channel=channel_id,
        topic=channel_topic
    )
    if not response.get("ok", False):
        raise SlackError('Fail to set channel topic for {} : {}'.format(channel_id, response['error']))

    return response


def unarchive_channel(channel_id):
    logger.error(f"Unarchive {channel_id}")
    response = slack_client.api_call(
        "conversations.unarchive",
        channel=channel_id,
    )
    logger.error(response)
    if not response.get("ok", False):
        raise SlackError(f"Couldn't unarchive channel {channel_id} : {response['error']}")

def archive_channel(channel_id):
    response = slack_client.api_call(
        "conversations.archive",
        channel=channel_id,
    )

    if not response.get("ok", False):
        raise SlackError(f"Couldn't archive channel {channel_id} : {response['error']}")



def get_or_create_channel(channel_name, auto_unarchive=False):
    try:
        return create_channel(channel_name)
    except SlackError:
        try:
            return get_channel_id(channel_name, auto_unarchive)
        except SlackError:
            return None


def send_message(channel_id, text, attachments=None, thread_ts=None):
    response = slack_client.api_call(
        "chat.postMessage",
        as_user=False,
        channel=channel_id,
        text=text,
        attachments=attachments,
        thread_ts=thread_ts,
    )
    if not response.get("ok", False):
        raise SlackError('Fail to send message to {} : {}'.format(channel_id, response['error']))

    return response


def send_ephemeral_message(channel_id, user_id, text, attachments=None):
    response = slack_client.api_call(
        "chat.postEphemeral",
        as_user=False,
        channel=channel_id,
        text=text,
        user=user_id,
        attachments=attachments,
    )
    if not response.get("ok", False):
        raise SlackError('Failed to send ephemeral message to {} : {}'.format(user_id, response['error']))
    return response


def add_reaction(reaction, channel_id, thread_ts):
    response = slack_client.api_call(
        "reactions.add",
        name=reaction,
        channel=channel_id,
        timestamp=thread_ts,
    )
    if not response.get("ok", False):
        if not response['error'] == 'already_reacted':
            raise SlackError('Failed to react with {} to message {} in thread {}: {}'.format(reaction, channel_id, thread_ts, response['error']))


def remove_reaction(reaction, channel_id, thread_ts):
    response = slack_client.api_call(
        "reactions.remove",
        name=reaction,
        channel=channel_id,
        timestamp=thread_ts,
    )

    if not response.get("ok", False):
        raise SlackError(f"Failed to remove reaction {reaction} from message {channel_id} in thread {thread_ts}: {response['error']}")


def invite_user_to_channel(user_id, channel_id):
    response = slack_client.api_call(
        "channels.invite",
        user=user_id,
        channel=channel_id
    )

    if not response.get("ok", False):
        raise SlackError('Failed to invite user <{}> to channel {} : {}'.format(user_id, channel_id, response['error']))


def get_slack_token_owner():
    """
    return the id of the user associated with the current slack token
    """
    response = slack_client.api_call(
        "auth.test",
    )
    if not response.get("ok", False):
        raise SlackError('Failed to get slack token owner {}'.format(response['error']))
    return response['user_id']


def leave_channel(channel_id):
    response = slack_client.api_call(
        "channels.leave",
        channel=channel_id
    )
    if not response.get("ok", False):
        raise SlackError('Failed to leave channel {} : {}'.format(channel_id, response['error']))


def get_user_profile(user_id):
    if not user_id:
        return None

    response = slack_client.api_call(
        "users.info",
        user=user_id
    )

    if not response.get("ok", False):
        raise SlackError('Failed to get user profile : {}'.format(response['error']))

    return {
        'id': user_id,
        'name': response['user']['name'],
        'fullname': response['user']['profile']['real_name'],
    }


def user_ref_to_username(value):
    """takes a <@U123ABCD> style ref and returns an @username"""
    # strip the '<@' and '>'
    user_id = reference_to_id(value.group())
    user_profile = get_user_profile(user_id)
    return '@' + user_profile['name'] or user_id


def slack_to_human_readable(value):
    # replace user references (<@U3231FFD>) with usernames (@chrisevans)
    value = re.sub(r"(<@U[A-Z0-9]+>)", user_ref_to_username, value)
    value = re.sub(r"(<#C[A-Z0-9]+\|([\-a-zA-Z0-9]+)>)", r"#\2", value)
    return value


def rename_channel(channel_id, new_name):
    prefix = ""
    if not (new_name.startswith("inc-") or new_name.startswith("#inc-")):
        prefix = "inc-"

    new_name = slugify(f"{prefix}{new_name}", max_length=21)

    response = slack_client.api_call(
        "channels.rename",
        channel=channel_id,
        name=new_name,
    )
    if not response.get("ok", False):
        raise SlackError(
            'Failed to rename channel : {}'.format(response['error']))
