
import os
import json

import requests
from flask import Flask, Response, request, make_response
from slackclient import SlackClient


SLACK_BOT_TOKEN = "....."
SLACK_VERIFICATION_TOKEN = "......"

slack_client = SlackClient(SLACK_BOT_TOKEN)


app = Flask(__name__)



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
                        "text": "existing group with email in csv",
                        "type": "button",
                        "value": "existing_group_with_email"
                    },
                    # {
                    #     "name": "game",
                    #     "text": "Remove me from existing group after specified duration",
                    #     "type": "button",
                    #     "value": "remove_from_group_or_channel_after_duration"
                    # },
                    # {
                    #     "name": "game",
                    #     "text": "Archive channel after a specified time",
                    #     "type": "button",
                    #     "value": "archive_channel_group_after_duration"
                    # },
                    # {
                    #     "name": "game",
                    #     "text": "Create channel and Archive channel after a specified time",
                    #     "type": "button",
                    #     "value": "create_and_archive_channel_group_after_duration"
                    # },
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



if __name__ == '__main__':
    app.run(debug=True)

# TODO:
# 1 throtthling to 50 request per minute
