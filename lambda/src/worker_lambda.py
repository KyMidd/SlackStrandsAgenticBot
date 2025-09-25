# Lambda handler function
import os
import json
from slack_bolt.adapter.aws_lambda import SlackRequestHandler


def isolate_event_body(event):
    # Dump the event to a string, then load it as a dict
    event_string = json.dumps(event, indent=2)
    event_dict = json.loads(event_string)

    # Isolate the event body from event package
    event_body = event_dict["body"]
    body = json.loads(event_body)

    # Return the event
    return body


def generate_response(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({"message": message}),
        "headers": {"Content-Type": "application/json"},
    }
