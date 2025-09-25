# Global imports
import os
import json

# Slack app imports
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

# Import all constants and configuration
from worker_inputs import *


###
# Local imports
###

from worker_slack import update_slack_response, register_slack_app
from worker_aws import (
    get_secret_with_client,
    create_bedrock_client,
    ai_request,
    enrich_guardrail_block,
)
from worker_agent import execute_agent
from worker_conversation import build_conversation_content, handle_message_event
from worker_lambda import isolate_event_body, generate_response


def lambda_handler(event, context):

    print("🚀 Lambda execution starting")

    # Isolate body
    event_body = isolate_event_body(event)

    # Print the event
    print("🚀 Event:", event)

    # Debug
    if debug_enabled == "True":
        print("🚀 Event body:", event_body)

    # Fetch secret package
    secrets = get_secret_with_client(os.environ.get("SECRET_NAME"), "us-east-1")

    # Decode, fetch token
    secrets_json = json.loads(secrets)
    token = secrets_json["SLACK_BOT_TOKEN"]

    # Register the Slack handler
    print("🚀 Registering the Slack handler")
    app, registered_bot_id = register_slack_app(
        token, secrets_json["SLACK_SIGNING_SECRET"]
    )

    # Register the AWS Bedrock AI client
    print("🚀 Registering the AWS Bedrock client")
    bedrock_client = create_bedrock_client(model_region_name)

    # Responds to app mentions
    @app.event("app_mention")
    def handle_app_mention_events(client, body, say):
        print("🚀 Handling app mention event")
        bedrock_client = create_bedrock_client(model_region_name)
        handle_message_event(
            client,
            event_body,
            say,
            bedrock_client,
            app,
            token,
            registered_bot_id,
            secrets_json,
        )

    # Respond to file share events
    @app.event("message")
    def handle_message_events(client, body, say, req):
        print("🚀 Handling message event")
        bedrock_client = create_bedrock_client(model_region_name)
        handle_message_event(
            client,
            event_body,
            say,
            bedrock_client,
            app,
            token,
            registered_bot_id,
            secrets_json,
        )

    # Initialize the handler
    print("🚀 Initializing the handler")
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
