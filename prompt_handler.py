"""Handles AI conversation logic, chat history, and command forwarding for Autoshell."""

import os
import threading
import tiktoken
import time
import app_globals
from sound_handler import SoundHandler

class PromptHandler:

    def __init__(self):
        # default settings for toggle buttons
        self.ask_for_execution = True
        self.follow_up_questions = False
        self.listen_to_keys = False
        self.pressed_key = None
        self.key_is_caught = False
        self.current_token_use = 0
        self.last_ai_response = None
        # globally accessible chat history
        self.chat_history = [
            {
                "role": "system",
                "content": PromptHandler.get_preprompt()
            }
        ]

    def get_preprompt(): 
        # load the preprompt from the external file
        os.chdir(app_globals.gui_handler_object.files_path)
        with open("pre_prompt_shell.txt", "r") as f:
            preprompt = f.read()
        os.chdir(app_globals.gui_handler_object.main_path)
        return preprompt
    
    def get_forwarding_prompt():
        # load the forwarding prompt from the external file
        os.chdir(app_globals.gui_handler_object.files_path)
        with open("pre_prompt_forwarder.txt", "r") as f:
            forwarding_prompt = f.read()
        os.chdir(app_globals.gui_handler_object.main_path)
        return forwarding_prompt

    def reset_chat_history(self):

        # reset last ai response
        self.last_ai_response = None

        # reset the chat history
        chat_history = [
            {
                "role": "system",
                "content": PromptHandler.get_preprompt()
            }
        ]
        return chat_history
    
    def add_to_chat_history(self, message, role):
        self.chat_history.append({
            "role": role,
            "content": message
        })

    # analyze the response from the llm and check if it is a shell command or a user message
    # we create a second agent that takes care of the forwarding decision
    def forward_by_ai(self, response_message):
        # create a new chat history with the forwarding prompt
        forwarding_chat_history = [
            {
                "role": "system",
                "content": PromptHandler.get_forwarding_prompt()
            }
        ]
        
        # add the last message to the forwarding chat history
        forwarding_chat_history.append({
            "role": "user",
            "content": response_message
        })

        # create a completion of the existing conversation, the agent will either answer "shell" or "user"
        answer_type = app_globals.openai_handler_object.generate_forwarding_decision(forwarding_chat_history, app_globals.openai_handler_object.OpenAiClient)

        # if the ai response is for the user, print it to the user Interace 
        if answer_type == "user":
            # if string goes like talk_to_user("message"), then clean it
            if response_message.startswith("talk_to_user("):
                clean_message = response_message[14:-2]
            else:
                clean_message = response_message

            PromptHandler.add_to_chat_history(clean_message, "assistant")
            
            app_globals.gui_handler_object.print_text(f"AI TO USER: \n{clean_message}\n\n", "white") 

            SoundHandler.text_to_speech(clean_message, app_globals.openai_handler_object.OpenAiClient, app_globals.sound_handler_object.voice_agent)

            # show the number of tokens used in the current conversation
            token_use = PromptHandler.num_tokens_from_string(str(self.chat_history), 'cl100k_base') #cl100k_base #p50k_base
            self.current_token_use = token_use
            token_max = 16384
            app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nTokens used: {token_use} / {token_max} ({round(token_use/token_max*100, 2)} %)\n\n", "light_blue")

            # save the message stream (here we are at the end of the conversation)
            PromptHandler.save_chat_history(self.chat_history)

            # if there are too many tokens used, then reset the chat history forcefully and let the user know
            if token_use > token_max-2000:
                self.chat_history = PromptHandler.reset_chat_history()
                app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nMaximum number of tokens reached, chat history reset.\n\n", "light_blue")
                

        # if the ai response is a command, forward it to the shell handler
        elif answer_type == "shell":
            # check if prompt handler is in "Ask Before Execution" mode
            if self.ask_for_execution:
                #gui
                app_globals.gui_handler_object.print_text(f"AI PROPOSAL: \n{response_message}\n\n", "green")
                app_globals.gui_handler_object.print_text("SYSTEM INFO: \nLet through? (y/n): \n", "light_blue")
                
                # define a function that listens to the keys of the UI, this function is run in a thread
                # It felt clunky and hacky but it works
                def listen_to_keys(response_message = response_message):
                    self.listen_to_keys = True
                    self.key_is_caught = False
                    while self.pressed_key is None and self.key_is_caught is False:
                        pass
                    
                    # save the key that was pressed
                    key = self.pressed_key
                    self.listen_to_keys = False

                    user_decision = key

                    # reset the key-catch-helpers
                    self.pressed_key = None
                    self.key_is_caught = False
                    self.listen_to_keys = False
                    
                    # if y or Y or enter is pressed, then forward the message to the shell
                    if user_decision == "y" or user_decision == "Y" or user_decision == "\r":
                        PromptHandler.add_to_chat_history(response_message, "assistant")
                        app_globals.shell_handler_object.execute(response_message)
                        
                        # give power shell answer back to the ai (this could create a loop)
                        response_message = app_globals.openai_handler_object.generate_AI_response(self.chat_history, app_globals.openai_handler_object.OpenAiClient)
                    else:
                        app_globals.gui_handler_object.print_text("SYSTEM INFO: \nShell execution blocked by user due to security issues.\n\n", "light_blue")
                        PromptHandler.add_to_chat_history(response_message, "assistant")
                        # save the message stream (here we are at the end of the conversation)
                        PromptHandler.save_chat_history(self.chat_history)


                # start a thread that listens to the keys
                threading.Thread(target=listen_to_keys).start()

            else:  # if not in ask for execution mode - forward everything to the shell
                app_globals.gui_handler_object.print_text(f"AI CODE: \n{response_message}\n\n", "green") 
                PromptHandler.add_to_chat_history(response_message, "assistant")
                app_globals.shell_handler_object.execute(response_message)
                
                # give power shell answer back to the ai (this could create a loop)
                response_message = app_globals.openai_handler_object.generate_AI_response(self.chat_history, app_globals.openai_handler_object.OpenAiClient)

        elif answer_type == "empty": # if the ai response is none, then do nothing
            app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nModel created empty reply message for the user.\n\n", "light_blue")
        else: # if the ai response is neither, then print a warning
            app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nDebug Warning: The forwarding decision is neither 'shell' nor 'user' but {answer_type}.\n\n", "light_blue")

    
    # save current message stream to a txt file, give it the current date and time as name
    def save_chat_history(chat_history):
        current_time = time.strftime("%d.%m.%Y-%Hh%Mm%Ss")

        # get current working directory
        cwd = os.getcwd()
        # go to subdirectory /logs
        subdirectory = "logs"
        path = os.path.join(cwd, subdirectory)
        os.chdir(path)

        # save as txt file in utf8 for compatibility with other languages
        with open(f"chat_history_{current_time}.txt", "w", encoding="utf-8") as f:
            #transform list of dictionaries into string
            chat_history_string = ""
            for item in chat_history:
                role = item["role"]
                text = item["content"]
                chat_history_string += f"\n{role}: {text}\n"
            f.write(chat_history_string)
            
        # go back to cwd
        os.chdir(cwd)
    
    # count the number of tokens in a string
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
