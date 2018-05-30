"""
WARNING: This code currently smell 💩 terribly it is an hackathon project would be refactored later 😄
"""

import os
import json
from datetime import datetime
import time

import requests
from config import Config
from flask import Flask, Response, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from slackclient import SlackClient
from zappa.async import task


# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]



# Slack client for Web API requests
slack_client = SlackClient(SLACK_BOT_TOKEN)


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


class EventDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True) # pylint: disable=no-member
    event_type = db.Column(db.String(64)) # pylint: disable=no-member
    user_initiated = db.Column(db.String(64)) # pylint: disable=no-member
    time_to_execute = db.Column(db.DateTime, default=datetime.utcnow) # pylint: disable=no-member
    acted_on = db.Column(db.Boolean, default=False) # pylint: disable=no-member
    # TODO: Are we supppose to allow null here answer while refactoring or if it breaks
    channel_or_group_id = db.Column(db.String(64)) # pylint: disable=no-member 
    
    def __repr__(self):
        return f"<Event {self.event_type} initiated by {self.user_initiated}>" 


@app.route("/")
def index():
    return "hello master P"


@app.route("/easy_add", methods=["GET", "POST"])
def easy_add():

    resp = {
        "text": "What would you like to do?",
        "attachments": [
            {
                "text": "Add Users to new group",
                "fallback": "You are unable to choose a game",
                "callback_id": "wopr_game",
                "color": "#3AA3E3",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "game",
                        "text": "New group with email",
                        "type": "button",
                        "value": "new_group_with_email"
                    },
                    {
                        "name": "game",
                        "text": "Existing group with email",
                        "type": "button",
                        "value": "existing_group_with_email"
                    },
                    {
                        "name": "game",
                        "text": "Eject from group after sometime",
                        "type": "button",
                        "value": "remove_from_group_or_channel_after_duration"
                    },
                    {
                        "name": "game",
                        "text": "Archive channel after time",
                        "type": "button",
                        "value": "archive_channel_group_after_duration"
                    },
                    {
                        "name": "game",
                        "text": "Create/Archive channel after",
                        "type": "button",
                        "value": "create_and_archive_channel_group_after_duration"
                    },
                    {
                        "name": "game",
                        "text": "Thermonuclear War",
                        "style": "danger",
                        "type": "button",
                        "value": "war",
                        "confirm": {
                            "title": "Are you sure?",
                            "text": "Wouldn't you prefer a good game of chess?",
                            "ok_text": "Yes",
                            "dismiss_text": "No"
                        }
                    }
                ]
            }
        ]
    }

    return Response(json.dumps(resp), mimetype="application/json")


def get_users_formatted_group(value_from_event):
    formatted_group = []
    user_groups = slack_client.api_call('groups.list')

    groups = user_groups.get('groups')

    for group in groups:
        formatted_group.append(
            {
                "text": group.get('name'),
                "value": f"{group.get('id')}-{group.get('name')}-Group-{value_from_event}"
            }
        )

    return formatted_group


def get_users_formatted_channel(value_from_event):
    formatted_channel = []
    user_channels = slack_client.api_call('channels.list')

    channels = user_channels.get('channels')

    # print("users channels are")
    # print(channels)

    for channel in channels:
        formatted_channel.append(
            {
                "text": channel.get('name'),
                "value": f"{channel.get('id')}-{channel.get('name')}-Channel-{value_from_event}"
            }
        )

    return formatted_channel


# TODO: Update this method
def create_menu_message():
    pass


def create_group(message_action):
    """
    Create Group from message action
    :Args: 
        message_action
    :Returns:
        str -- Returns the group Id
    """
    created_group_details = slack_client.api_call(
        "groups.create",
        name=message_action['submission'].get('grp_or_channel_name'),
        validate=True
    )
    print("time to print group")
    # {'ok': False, 'error': 'name_taken', 'detail': '`name` is already taken.'}
    # Handle this kind of error
    print(created_group_details)
    group_id = created_group_details.get('group')['id']

    return group_id


@task
def add_users_to_group_by_email(message_action, group_id, response_url):
    # Invite users to group
    emails = message_action['submission'].get('email').splitlines()
    # Get users by email
    # if emails:
    for email in emails:
        print(f"email is {email}")
        get_user = slack_client.api_call(
            "users.lookupByEmail",
            email=email
        )
        # print(f"User object is {get_user}")
        add_to_group = slack_client.api_call(
            "groups.invite",
            channel=group_id,
            user=get_user['user']['id']
        )

        print(group_id)
        print("add to group")
        print(add_to_group)
    data = {
        'response_type': 'in_channel',
        'text': '*Users* are currently being added :smile: _easy_add_ does it.',
    }
    requests.post(response_url, json=data)


def get_formatted_time(time_to_use):
    return datetime.utcnow()

# Temporarily adding this since it will involve a db call
# @task
# def add_event_details(message_action, channel_or_group_id, response_url, value_from_event):

#     event_details = EventDetails(
#         event_type=value_from_event,
#         user_initiated=message_action['user']['id'],
#         time_to_execute=get_formatted_time(message_action['submission']['days_to_remove']),
#         channel_or_group_id=channel_or_group_id
#     )
#     db.session.add(event_details) # pylint: disable=no-member
#     db.session.commit() # pylint: disable=no-member
#     execute_event(response_url)

#     data = {
#         'response_type': 'in_channel',
#         'text': '*Users* are currently being added :smile: _easy_add_ does it.',
#     }
#     requests.post(response_url, json=data)


@task
def remove_from_group_pass(message_action, response_url):
    # TODO Handle both group or channel
    callback_id = message_action.get('callback_id')
    time_before_sleep = message_action['submission']['days_to_remove']
    # 'GAJASLX18-remove_from_group_or_channel_after_duration'
    
    time.sleep(int(time_before_sleep))
    channel_or_group_id = callback_id.split('-')[0]
    remove_user = slack_client.api_call(
        "groups.kick",
        user=message_action['user']['id'],
        channel=channel_or_group_id
    )
    print(remove_user)
    
    data = {
        'response_type': 'in_channel',
        'text': '*Users* are currently being added :smile: _easy_add_ does it.',
    }
    requests.post(response_url, json=data)

@task
def archive_channel_or_group(message_action, response_url):
    # TODO: handle from group or channel
    # handle remove from group or channel
    callback_id = message_action.get('callback_id')
    time_before_sleep = message_action['submission']['days_to_remove']
    # 'GAJASLX18-remove_from_group_or_channel_after_duration'
    channel_or_group_id = callback_id.split('-')[0]
    time.sleep(int(time_before_sleep))

    archive_channel_or_group = slack_client.api_call(
        "groups.archive",
        channel=channel_or_group_id
    )
    print(archive_channel_or_group)
    data = {
        'response_type': 'in_channel',
        'text': '*Users* are currently being added :smile: _easy_add_ does it.',
    }
    requests.post(response_url, json=data)

def execute_event(response_url):
    # remove response url after test
    # Also filter by time passed
    events = EventDetails.query.filter_by(acted_on=False)
    for event in events:
        
        if event.event_type == "remove_from_group_or_channel_after_duration":
            remove_from_group_pass(event, response_url)
        elif event.event_type == "archive_channel_group_after_duration":
            archive_channel_or_group(event, response_url)



@app.route("/components", methods=["GET", "POST"])
def components():
    print(json.loads(request.form["payload"]))
    message_action = json.loads(request.form["payload"])

    if message_action.get('type') == 'interactive_message':
        action = message_action['actions'][0]
        trigger_id = message_action["trigger_id"]
        if action.get('selected_options'):
            if message_action.get('callback_id') == 'remove_from_group_or_channel_after_duration':
                value_from_select_option = action['selected_options'][0]['value'].split('-')
                group_or_channel_id, name, group_or_channel, value_from_event = value_from_select_option[
                    0], value_from_select_option[1], value_from_select_option[2], value_from_select_option[3]
                open_dialog = slack_client.api_call(
                    "dialog.open",
                    trigger_id=trigger_id,
                    dialog={
                        # "callback_id": message_action['callback_id'],
                        "callback_id": f"{group_or_channel_id}-{value_from_event}",
                        "title": f"Remove from {name}",
                        "submit_label": "Remove",
                        "elements": [
                            {
                                "type": "text",
                                "label": "Seconds to remove",
                                "subtype": "number",
                                "placeholder": "Seconds before I am removed from group",
                                "name": "days_to_remove"
                            }
                        ]
                    }

                )
                print(open_dialog)
            
            elif message_action.get('callback_id') == 'archive_channel_group_after_duration':
                value_from_select_option = action['selected_options'][0]['value'].split('-')
                group_or_channel_id, name, group_or_channel, value_from_event = value_from_select_option[
                    0], value_from_select_option[1], value_from_select_option[2], value_from_select_option[3]
                open_dialog = slack_client.api_call(
                    "dialog.open",
                    trigger_id=trigger_id,
                    dialog={
                        # "callback_id": message_action['callback_id'],
                        "callback_id": f"{group_or_channel_id}-{value_from_event}",
                        "title": f"Archive {name}",
                        "submit_label": f"Archive",
                        "elements": [
                            {
                                "type": "text",
                                "label": "When to archive",
                                "subtype": "number",
                                "placeholder": "Seconds before archiving",
                                # TODO: don't forget add_event_details when refactoring
                                # refactor to use days_to_archive
                                "name": "days_to_remove"
                            }
                        ]
                    }

                )
                print(open_dialog)
            elif message_action.get('callback_id') == 'existing_group_with_email':
                # put extra conditionals here for the several conditions
                # add to existing group with email
                # remove from group or channel after duration
                # archive channel or group after duration
                print("I got to the selection options")
                print(f"selected value is {action['selected_options']}")
                value_from_select_option = action['selected_options'][0]['value'].split(
                    '-')
                group_or_channel_id, name, group_or_channel, value_from_event = value_from_select_option[
                        0], value_from_select_option[1], value_from_select_option[2], value_from_select_option[3]
                open_dialog = slack_client.api_call(
                    "dialog.open",
                    trigger_id=trigger_id,
                    dialog={
                        # "callback_id": message_action['callback_id'],
                        "callback_id": f"{group_or_channel_id}-{value_from_event}",
                        "title": f"Add to {name} {group_or_channel}",
                        "submit_label": "Invite",
                        "elements": [
                            {
                                "type": "textarea",
                                "label": "Emails",
                                "name": "email"
                            }
                        ]
                    }

                )
                print(open_dialog)
        elif action.get('value'):
            user_id = message_action["user"]["id"]
            print(f"The user id is {user_id}")

            if action['value'] == 'new_group_with_email':
                print(f"action value is {action['value']}")
                open_dialog = slack_client.api_call(
                    "dialog.open",
                    trigger_id=trigger_id,
                    dialog={
                        "callback_id": action['value'],
                        # "callback_id": message_action['callback_id'],
                        "title": "Create a group",
                        "submit_label": "Create",
                        "elements": [
                            {
                                "type": "text",
                                "label": "Group Name",
                                "name": "grp_or_channel_name"
                            },

                            {
                                "type": "textarea",
                                "label": "Emails",
                                "name": "email"
                            }
                        ]
                    }
                )

            elif action['value'] == 'existing_group_with_email':
                users_group = get_users_formatted_group(action['value'])
                users_channel = get_users_formatted_channel(action['value'])

                users_group.extend(users_channel)

                menu_options = {
                    "text": "Select a channel/group to join",
                    "response_type": "in_channel",
                    "attachments": [
                        {
                            "text": "Pick a channel/group to join",
                            "fallback": "If you could read this message, you'd be choosing something fun to do right now.",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "callback_id": "existing_group_with_email",
                            "actions": [
                                {
                                    "name": "games_list",
                                    "text": "Pick a channel/group...",
                                    "type": "select",
                                    "option_groups": [
                                        {
                                            "text": "Channels",
                                            "options": users_channel
                                        },
                                        {
                                            "text": "Groups",
                                            "options": users_group
                                        }
                                    ]

                                }
                            ]
                        }
                    ]
                }

                return Response(json.dumps(menu_options), mimetype='application/json')

            elif action['value'] == 'remove_from_group_or_channel_after_duration':
                users_group = get_users_formatted_group(action['value'])
                users_channel = get_users_formatted_channel(action['value'])

                users_group.extend(users_channel)
                # Get channel and trigger a dialog that user can enter duration to stay in channel
                menu_options = {
                    "text": "Select a channel/group to remove from",
                    "response_type": "in_channel",
                    "attachments": [
                        {
                            "text": "Pick a channel/group to remove from",
                            "fallback": "If you could read this message, you'd be choosing something fun to do right now.",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "callback_id": "remove_from_group_or_channel_after_duration",
                            "actions": [
                                {
                                    "name": "games_list",
                                    "text": "Pick a channel/group...",
                                    "type": "select",
                                    "option_groups": [
                                        {
                                            "text": "Channels",
                                            "options": users_channel
                                        },
                                        {
                                            "text": "Groups",
                                            "options": users_group
                                        }
                                    ]

                                }
                            ]
                        }
                    ]
                }

                return Response(json.dumps(menu_options), mimetype='application/json')

            elif action['value'] == 'archive_channel_group_after_duration':
                users_group = get_users_formatted_group(action['value'])
                users_channel = get_users_formatted_channel(action['value'])

                users_group.extend(users_channel)
                menu_options = {
                    "text": "Archive group/channel (You can only archive channel/group you created)",
                    "response_type": "in_channel",
                    "attachments": [
                        {
                            "text": "Choose a channel",
                            "fallback": "If you could read this message, you'd be choosing something fun to do right now.",
                            "color": "#3AA3E3",
                            "attachment_type": "default",
                            "callback_id": "archive_channel_group_after_duration",
                            "actions": [
                                {
                                    "name": "games_list",
                                    "text": "Pick a channel",
                                    "type": "select",
                                    "option_groups": [
                                        {
                                            "text": "Channels",
                                            "options": users_channel
                                        },
                                        {
                                            "text": "Groups",
                                            "options": users_group
                                        }
                                    ]

                                }
                            ]
                        }
                    ]
                }

                return Response(json.dumps(menu_options), mimetype='application/json')
            elif action['value'] == 'create_and_archive_channel_group_after_duration':
                # This dialog should just have a text field and a drop down/ text field with hours and days selected
                # Coming soon feature
                data = {
                    'response_type': 'in_channel',
                    'text': 'This feature is coming soon keep your _fingers crossed_ :crossed_fingers: .',
                }
                requests.post(message_action['response_url'], json=data)
                
    elif message_action.get('type') == 'dialog_submission':
        # TODO: v2 create a drop down to enable creating a group or channel
        # handle 
        #
        print("current message action")
        print(message_action)
        response_url = message_action['response_url']

        # if message_action['submission'].get('grp_or_channel_name'):
        if message_action['callback_id'] == "new_group_with_email":
            # For version 1 creating group alone for *new*
            group_id = create_group(message_action)
            add_users_to_group_by_email(message_action, group_id, response_url)
        else:
            group_or_channel_id, value_from_event = message_action['callback_id'].split('-')[0], message_action['callback_id'].split('-')[1]
            if value_from_event == "existing_group_with_email":
                add_users_to_group_by_email(message_action, group_or_channel_id, response_url)
            elif value_from_event == "remove_from_group_or_channel_after_duration":
                print(f"This is the current value from event {value_from_event}")
                print(value_from_event)
                print(message_action)
                remove_from_group_pass(message_action, response_url)
                # add_event_details(message_action, group_or_channel_id, response_url, value_from_event)
            elif value_from_event == "archive_channel_group_after_duration":
                #TODO Do an extra check for the user that created it
                print(f"This is the current value from event {value_from_event}")
                print(message_action)
                archive_channel_or_group(message_action, response_url)
                # add_event_details(message_action, group_or_channel_id, response_url, value_from_event)
                

        # Check if it is group or channel
        # Create channel
        # create_channel = slack_client.api_call(
        #     "channels.create",
        #     name=message_action['submission'].get('grp_or_channel_name'),
        #     validate=True
        # )

        
        # rpost = requests.post(response_url, json={'text': 'new message', 'attachments': []})
        # rpost = requests.post(response_url, json={
        #     "response_type": "ephemeral",
        #     "text": "Sorry, that didn't work. Please try again."
        # })
        # print("post response")
        # print(rpost.json())
        # print(dir(rpost))
        # {text: 'new message', attachments: [...]}.to_json

        # return Response(json.dumps(rpost), mimetype="application/json")

        # return make_response(json.dumps(rpost.json()), 200)
        # return Response(rpost, mimetype="application/json")
    return make_response("", 200)
    
# Boto bucket name shouldn't have underscore 💩
# ClientError: An error occurred (InvalidBucketName) when calling the CreateBucket operation: The specified bucket is not valid.

if __name__ == '__main__':
    app.run(debug=True)


# TODO:
# Title in dialog.open cannot be longer than 24 characters investigate and fix
# throttling issues
# Update necessary callbackids
# Handle all these conditionality properly. this code is so messy smells like 💩
# Inspect zappa settings for events stuff
# existing group bug


# from app import EventDetails
# from app import db
# 