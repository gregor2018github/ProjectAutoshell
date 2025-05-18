"""Create a connection to the OpenAI API and handle the responses."""

import os
from openai import OpenAI
from prompt_handler import PromptHandler
import app_globals 

# connection to Open AI API
class OpenAiHandler:

    def __init__(self):
        self.OpenAiClient = OpenAI(
            api_key=os.environ['OPENAI_API_KEY'],
        )

    def generate_AI_response(chat_history, client):
        # create a completion of the existing conversation
        response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k", #gpt-3.5-turbo-1106 ; gpt-3.5-turbo-16k ; gpt-3.5-turbo
        messages=chat_history,
        temperature=1.01,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )

        response_message = response.choices[0].message.content 

        # check if the response is the same as the last one
        if response_message == app_globals.prompt_handler_object.last_ai_response:
            # if so, then reset the chat history
            app_globals.prompt_handler_object.chat_history = PromptHandler.reset_chat_history()
            app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nSame AI response as last time, chat history reset.\n\n", "light_blue")

        # check if message needs to be forwarded to the user or to the shell
        PromptHandler.forward_by_ai(response_message)

    
    def generate_forwarding_decision(forwarding_chat_history, client):
        # create a completion of the existing conversation
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=forwarding_chat_history,
        temperature=1.01,
        max_tokens=5,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )

        response_message = response.choices[0].message.content 
        return response_message
