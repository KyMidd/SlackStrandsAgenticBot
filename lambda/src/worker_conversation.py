# Conversation handling functions
import os
import requests
from worker_slack import update_slack_response, delete_slack_response
from worker_agent import execute_agent
from worker_aws import ai_request
from worker_inputs import debug_enabled


def build_conversation_content(payload, token):
    # Initialize unsupported file type found canary var
    unsupported_file_type_found = False

    # Debug
    if debug_enabled == "True":
        print("🚀 Conversation content payload:", payload)

    # Initialize the content array
    content = []

    # Initialize pronouns as blank
    pronouns = ""

    # Initialize bot_id as blank
    bot_id = ""

    # Identify user_id
    user_id = payload["user"]
    speaker_name = user_id  # Default speaker name if user info cannot be fetched

    # Fetch user information from Slack API
    user_info = requests.get(
        f"https://slack.com/api/users.info?user={user_id}",
        headers={"Authorization": "Bearer " + token},
    )
    user_info_json = user_info.json()

    # Debug
    if debug_enabled == "True":
        print("🚀 Conversation content user info:", user_info_json)

    # Identify the speaker's name based on their profile data
    profile = user_info_json.get("user", {}).get("profile", {})
    display_name = profile.get("display_name")
    real_name = user_info_json.get("user", {}).get("real_name", "Unknown User")
    speaker_name = display_name or real_name

    # If bot, set pronouns as "Bot"
    if "bot_id" in user_info_json:
        pronouns = " (Bot)"
    else:
        # Pronouns
        try:
            # If user has pronouns, set to pronouns with round brackets with a space before, like " (they/them)"
            pronouns = f" ({profile['pronouns']})"
        except:
            # If no pronouns, use the initialized pronouns (blank)
            if debug_enabled == "True":
                print("🚀 User has no pronouns, using blank pronouns")

    # If text is not empty, and text length is greater than 0, append to content array
    if "text" in payload and len(payload["text"]) > 1:
        # If debug variable is set to true, print the text found in the payload
        if debug_enabled == "True":
            print("🚀 Text found in payload: " + payload["text"])

        content.append(
            {
                # Combine the user's name with the text to help the model understand who is speaking
                "text": f"{speaker_name}{pronouns} says: {payload['text']}",
            }
        )

    if "attachments" in payload:
        # Append the attachment text to the content array
        for attachment in payload["attachments"]:

            # If debug variable is set to true, print the text found in the attachments
            if debug_enabled == "True" and "text" in attachment:
                print("🚀 Text found in attachment: " + attachment["text"])

            # Check if the attachment contains text
            if "text" in attachment:
                # Append the attachment text to the content array
                content.append(
                    {
                        # Combine the user's name with the text to help the model understand who is speaking
                        "text": f"{speaker_name}{pronouns} says: "
                        + attachment["text"],
                    }
                )

    # If the payload contains files, iterate through them
    if "files" in payload:

        # Append the payload files to the content array
        for file in payload["files"]:

            # Debug
            if debug_enabled == "True":
                print("🚀 File found in payload:", file)

            # Isolate name of the file and remove characters before the final period
            file_name = file["name"].split(".")[0]

            # File is a supported type
            file_url = file["url_private_download"]

            # Fetch the file and continue
            file_object = requests.get(
                file_url, headers={"Authorization": "Bearer " + token}
            )

            # Decode object into binary file
            file_content = file_object.content

            # Check the mime type of the file is a supported image file type
            if file["mimetype"] in [
                "image/png",  # png
                "image/jpeg",  # jpeg
                "image/gif",  # gif
                "image/webp",  # webp
            ]:

                # Isolate the file type based on the mimetype
                file_type = file["mimetype"].split("/")[1]

                # Append the file to the content array
                content.append(
                    {
                        "image": {
                            "format": file_type,
                            "source": {
                                "bytes": file_content,
                            },
                        }
                    }
                )

            # Check if file is a supported document type
            elif file["mimetype"] in [
                "application/pdf",
                "application/csv",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/html",
                "text/markdown",
            ]:

                # Isolate the file type based on the mimetype
                if file["mimetype"] in ["application/pdf"]:
                    file_type = "pdf"
                elif file["mimetype"] in ["application/csv"]:
                    file_type = "csv"
                elif file["mimetype"] in [
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ]:
                    file_type = "docx"
                elif file["mimetype"] in [
                    "application/vnd.ms-excel",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ]:
                    file_type = "xlsx"
                elif file["mimetype"] in ["text/html"]:
                    file_type = "html"
                elif file["mimetype"] in ["text/markdown"]:
                    file_type = "markdown"

                # Append the file to the content array
                content.append(
                    {
                        "document": {
                            "format": file_type,
                            "name": file_name,
                            "source": {
                                "bytes": file_content,
                            },
                        }
                    }
                )

                # Append the required text to the content array
                content.append(
                    {
                        "text": "file",
                    }
                )

            # Support plaintext snippets
            elif file["mimetype"] in ["text/plain"]:
                # File is a supported type
                snippet_file_url = file["url_private_download"]

                # Fetch the file and continue
                snippet_file_object = requests.get(
                    snippet_file_url, headers={"Authorization": "Bearer " + token}
                )

                # Decode the file into plaintext
                snippet_text = snippet_file_object.content.decode("utf-8")

                # Append the file to the content array
                content.append(
                    {
                        "text": f"{speaker_name} {pronouns} attached a snippet of text:\n\n{snippet_text}",
                    }
                )

            # If the mime type is not supported, set unsupported_file_type_found to True
            else:
                print(f"Unsupported file type found: {file['mimetype']}")
                unsupported_file_type_found = True
                continue

    # Return
    return bot_id, content, unsupported_file_type_found


def build_conversation_context(body, token, registered_bot_id, app):
    """Build conversation context with full thread history"""

    conversation = []

    # Check for thread context
    if "thread_ts" in body["event"]:
        # Get thread messages using app client
        thread_ts = body["event"]["thread_ts"]
        messages = app.client.conversations_replies(
            channel=body["event"]["channel"], ts=thread_ts
        )

        # Iterate through every message in the thread
        for message in messages["messages"]:
            # Build the content array
            (
                bot_id_from_message,
                thread_conversation_content,
                unsupported_file_type_found,
            ) = build_conversation_content(message, token)

            if debug_enabled == "True":
                print("🚀 Thread conversation content:", thread_conversation_content)

            # Check if the thread conversation content is empty
            if thread_conversation_content != []:
                # Check if message came from our bot
                if bot_id_from_message == registered_bot_id:
                    conversation.append(
                        {
                            "role": "assistant",
                            "content": [{"text": message["text"]}],
                        }
                    )
                # If not, the message came from a user
                else:
                    # Convert thread_conversation_content to simple text if it's a list
                    if isinstance(thread_conversation_content, list):
                        # Extract text from content blocks if needed
                        content_text = ""
                        for item in thread_conversation_content:
                            if isinstance(item, dict) and "text" in item:
                                content_text += item["text"]
                            elif isinstance(item, str):
                                content_text += item
                        user_content = content_text if content_text else "Empty message"
                    else:
                        user_content = (
                            str(thread_conversation_content)
                            if thread_conversation_content
                            else "Empty message"
                        )

                    conversation.append(
                        {
                            "role": "user",
                            "content": (
                                [{"text": user_content}]
                                if isinstance(user_content, str)
                                else user_content
                            ),
                        }
                    )

                    if debug_enabled == "True":
                        print(
                            "🚀 State of conversation after threaded message append:",
                            conversation,
                        )
    else:
        # Single message conversation
        event = body["event"]
        bot_id_from_message, user_conversation_content, unsupported_file_type_found = (
            build_conversation_content(event, token)
        )

        # Convert to simple text format for Strands
        if isinstance(user_conversation_content, list):
            content_text = ""
            for item in user_conversation_content:
                if isinstance(item, dict) and "text" in item:
                    content_text += item["text"]
                elif isinstance(item, str):
                    content_text += item
            user_content = content_text if content_text else "Empty message"
        else:
            user_content = (
                str(user_conversation_content)
                if user_conversation_content
                else "Empty message"
            )

        conversation.append(
            {
                "role": "user",
                "content": (
                    [{"text": user_content}]
                    if isinstance(user_content, str)
                    else user_content
                ),
            }
        )

    return conversation


def handle_message_event(
    client, body, say, bedrock_client, app, token, registered_bot_id, secrets_json
):
    from worker_inputs import (
        bot_name,
        enable_initial_model_context_step,
        initial_model_user_status_message,
        initial_model_system_prompt,
    )

    # Initialize message_ts as None
    # This is used to track the slack message timestamp for updating the message
    message_ts = None

    channel_id = body["event"]["channel"]
    event = body["event"]

    # Determine the thread timestamp
    thread_ts = body["event"].get("thread_ts", body["event"]["ts"])

    # Initialize conversation context
    conversation = []

    # Check to see if we're in a thread
    # If yes, read previous messages in the thread, append to conversation context for AI response
    if "thread_ts" in body["event"]:
        # Get the messages in the thread
        thread_ts = body["event"]["thread_ts"]
        messages = app.client.conversations_replies(
            channel=body["event"]["channel"], ts=thread_ts
        )

        # Iterate through every message in the thread
        for message in messages["messages"]:

            # Build the content array
            (
                bot_id_from_message,
                thread_conversation_content,
                unsupported_file_type_found,
            ) = build_conversation_content(message, token)

            if debug_enabled == "True":
                print("🚀 Thread conversation content:", thread_conversation_content)

            # Check if the thread conversation content is empty. This happens when a user sends an unsupported doc type only, with no message
            if thread_conversation_content != []:
                # Conversation content is not empty, append to conversation

                # Check if message came from our bot
                # We're assuming our bot only generates text content, which is true of Claude v3.5 Sonnet v2
                if bot_id_from_message == registered_bot_id:
                    conversation.append(
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "text": message["text"],
                                }
                            ],
                        }
                    )
                # If not, the message came from a user
                else:
                    conversation.append(
                        {"role": "user", "content": thread_conversation_content}
                    )

                    if debug_enabled == "True":
                        print(
                            "🚀 State of conversation after threaded message append:",
                            conversation,
                        )

    else:
        # We're not in a thread, so we just need to add the user's message to the conversation

        # Build the user's part of the conversation
        bot_id_from_message, user_conversation_content, unsupported_file_type_found = (
            build_conversation_content(event, token)
        )

        # Append to the conversation
        conversation.append(
            {
                "role": "user",
                "content": user_conversation_content,
            }
        )

        if debug_enabled == "True":
            print("🚀 State of conversation after append user's prompt:", conversation)

    # Check if conversation content is empty, this happens when a user sends an unsupported doc type only, with no message
    # Conversation looks like this: [{'role': 'user', 'text': []}]
    if debug_enabled == "True":
        print("🚀 State of conversation before check if convo is empty:", conversation)
    if conversation == []:
        # Conversation is empty, append to error message
        if debug_enabled == "True":
            print("🚀 Conversation is empty, exiting")

        # Announce the error
        say(
            text=f"> `Error`: Unsupported file type found, please ensure you are sending a supported file type. Supported file types are: images (png, jpeg, gif, webp).",
            thread_ts=thread_ts,
        )
        return

    # Before we fetch the knowledge base, do an initial turn with the AI to add context
    if enable_initial_model_context_step:
        message_ts = update_slack_response(
            say,
            client,
            message_ts,
            channel_id,
            thread_ts,
            initial_model_user_status_message,
        )

        # Ask the AI for a response
        ai_response = ai_request(
            bedrock_client,
            conversation,
            say,
            thread_ts,
            client,
            message_ts,
            channel_id,
            initial_model_system_prompt,
        )

        # Append to conversation
        conversation.append(
            {
                "role": "assistant",
                "content": [
                    {
                        "text": f"Initialization information from the model: {ai_response}",
                    }
                ],
            }
        )

        # Debug
        if debug_enabled == "True":
            print("🚀 State of conversation after context request:", conversation)

    # Initial message to user
    initial_message = f"🚀 {bot_name} is connecting to platforms and analyzing your request.\n\n{bot_name} can be slow, since she's connecting to platforms and using tools. Please give her 1-2 minutes to respond.\n\nWhen {bot_name} has finished, Slack will alert you of a new message in this thread.\n\n:turtle::turtle::turtle::turtle::turtle::turtle::turtle::turtle::turtle::turtle:"
    message_ts = update_slack_response(
        say,
        client,
        message_ts,
        channel_id,
        thread_ts,
        initial_message,
    )

    # Build conversation in bedrock format
    conversation = build_conversation_context(body, token, registered_bot_id, app)

    # Execute bedrock agent to fetch response
    response = execute_agent(
        secrets_json,
        conversation,
    )

    # Delete the initial "researching" message
    delete_slack_response(client, channel_id, message_ts)

    # Update Slack with final response
    message_ts = update_slack_response(
        say, client, None, channel_id, thread_ts, response
    )

    print("🚀 Successfully completed response")
    return
