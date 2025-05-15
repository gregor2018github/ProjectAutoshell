"""
DESCRIPTION:

This Python script creates an AI assistant that can interact with your computer's PowerShell. It's called "Autoshell". 
The assistant is capable of understanding your voice, executing commands in the PowerShell, and answering via speech synthesis. 
This approach provides a nearly hands-free way to control your PC. The user steers the conversation via a GUI.

The program allows for a wide range of functionalities, like:
    - opening applications
    - get specifications about your PC (e.g. battery level, hardware components, network connections etc.)
    - create files and folders, navigate through your file system
    - shutdown, restart, log off, lock your PC
    - write and run little scripts
    - just chat with it in multiple languages
    - many more to discover... feel free to play around with it!

The AI models are provided by OpenAI's API. The execution of the program will cost money and your data will be forwarded to OpenAI's servers.
In order to run the models you need to create an account and get a resepctive API key.
The API key needs to be stored in an environment variable called "OPENAI_API_KEY"! 
Furthermore, you need an internet connection to run the program.

The program uses the following AI models:
    - GPT-3.5 to generate text (16k tokens context length)
    - Whisper to understand the user's voice
    - TTS1 (6 different voice models) to synthesize speech

The autoshell.exe needs to be in a directory with the folders "logs" and "files" whereby "files" needs to contain the following files: 
    - audio_dummy.wav
    - 6 voice model examples (example_alloy.mp3, example_echo.mp3, example_fable.mp3, example_nova.mp3, example_shimmer.mp3, example_onyx.mp3)
    - pre_prompt_shell.txt
    - pre_prompt_forwarder.txt

20.01.2024
"""

"""
- process the sound output as a subprocess, so that it won't freeze the program
- try to give admin rights to the shell process
"""

from openai import OpenAI
import os
import pyaudio
from pygame import mixer
import subprocess
import threading
import tiktoken
import time
import tkinter as tk
from tkinter import PhotoImage
from tkinter import ttk
import wave

# a guided user interface
class GuiHandler:
    def __init__(self):
        # Initialize the mixer module for playing sound
        mixer.init()
        
        # Create the main window
        root = tk.Tk()
        root.title("Autoshell")
        # check the size of the current screen
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        # make the window cover the whole screen
        root.geometry("%dx%d" % (round(width/2,0), round(height/2,0)))

        # load it into the class
        self.root = root

        # Load the image file
        # file path is current path + /files + /background_image.png
        picture_path = os.path.join(os.getcwd(), "files", "background_image.png")
        bg_image = PhotoImage(file=picture_path)
        # Create a label with the image
        bg_label = tk.Label(self.root, image=bg_image)
        # Keep a reference to the image to prevent it from being garbage collected
        bg_label.image = bg_image
        # Place the label on the window
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # add elements to UI
        self.create_start_stop_record_button()
        self.create_toggle_button()
        self.create_toogle_button_two()
        self.create_voice_dropdown()
        self.create_text_window()

        # create two paths, the main path and the subdirectory path for files
        self.main_path = os.getcwd()
        self.files_path = os.path.join(self.main_path, "files")
        self.log_path = os.path.join(self.main_path, "logs")

        # bind the key listening function to the gui
        self.root.bind("<Key>", self.key_pressed)

    def play_sound(self, file_name):
        os.chdir(self.files_path)
        # make a copy of the file so that it can be overwritten
        mixer.music.load(file_name)  # Load the sound file
        mixer.music.play()  # Play the sound file
        # wait until the sound is finished playing
        while mixer.music.get_busy():
            pass
        # load a dummy file so that the "generated_audio.mp3" can be overwritten and be used again
        mixer.music.load("audio_dummy.wav")
        os.chdir(self.main_path)
    
    def print_text(self, text, color):
        
        self.text_field.config(state="normal")

        if color == "green":
            self.text_field.insert(tk.END, text, "tag_green")
        elif color == "red":
            self.text_field.insert(tk.END, text, "tag_red")
        elif color == "white":
            self.text_field.insert(tk.END, text, "tag_white")
        elif color == "blue":
            self.text_field.insert(tk.END, text, "tag_blue")
        elif color == "light_blue":
            self.text_field.insert(tk.END, text, "tag_light_blue")
        
        # refresh the text field
        self.text_field.update_idletasks()
        self.text_field.see(tk.END)

        # remove reactivity of the text field so that the user can not edit it
        self.text_field.config(state="disabled")

    def toggle_record(self):
        # Toggle the recording state
        if self.record_state == 'start':
            self.start_record()
            self.record_button.config(text="Stop Recording 🎤")
            self.record_state = 'stop'
        else:
            self.stop_record()
            self.record_button.config(text="Start Recording 🎤")
            self.record_state = 'start'

    def start_record(self):
        # Start recording
        sound_handler.start_recording("audio_record")
    
    def stop_record(self):
        # Stop recording
        sound_handler.stop_recording()

        # if follow up questions are enabled, then do not reset the chat history
        if not prompt_handler.follow_up_questions:
            prompt_handler.chat_history = PromptHandler.reset_chat_history()

        # use speech to text method to get the text from the recorded audio
        user_input = SoundHandler.speech_to_text("audio_record.wav", openai_handler.OpenAiClient)

        # print user input to gui, then generate ai response
        gui_handler.print_text(f"USER: \n{user_input}\n\n", "white")
        PromptHandler.add_to_chat_history(user_input, "user")
        OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)

    def toggle_execution(self):
        # Toggle the execution mode
        if self.toggle_state.get() == 1:
            prompt_handler.ask_for_execution = False
            gui_handler.print_text("SYSTEM INFO: \nDirect Code Execution Enabled\n\n", "light_blue")
        else:
            prompt_handler.ask_for_execution = True
            gui_handler.print_text("SYSTEM INFO: \nDirect Code Execution Disabled\n\n", "light_blue")
    
    def toggle_execution_two(self):
        # toggle follow up question mode
        if self.toggle_state_two.get() == 1:
            prompt_handler.follow_up_questions = True
            gui_handler.print_text("SYSTEM INFO: \nFollow-Up Questions Enabled\n\n", "light_blue")
        else:
            prompt_handler.follow_up_questions = False
            gui_handler.print_text("SYSTEM INFO: \nFollow-Up Questions Disabled\n\n", "light_blue")        

    def change_voice(self, voice):
        # change the voice of the ai
        if voice == "Voice = Onyx":
            sound_handler.voice_agent = "onyx"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Onyx.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_onyx.mp3")
            os.chdir(gui_handler.main_path)
        elif voice == "Voice = Alloy":
            sound_handler.voice_agent = "alloy"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Alloy.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_alloy.mp3")
            os.chdir(gui_handler.main_path)
        elif voice == "Voice = Echo":
            sound_handler.voice_agent = "echo"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Echo.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_echo.mp3")
            os.chdir(gui_handler.main_path)
        elif voice == "Voice = Fable":
            sound_handler.voice_agent = "fable"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Fable.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_fable.mp3")
            os.chdir(gui_handler.main_path)
        elif voice == "Voice = Nova":
            sound_handler.voice_agent = "nova"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Nova.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_nova.mp3")
            os.chdir(gui_handler.main_path)
        elif voice == "Voice = Shimmer":
            sound_handler.voice_agent = "shimmer"
            gui_handler.print_text("SYSTEM INFO: \nVoice changed to Shimmer.\n\n", "light_blue")
            # play a sample sound
            os.chdir(gui_handler.files_path)
            gui_handler.play_sound("example_shimmer.mp3")
            os.chdir(gui_handler.main_path)

    # define what happens when a key is pressed
    def key_pressed(self, event):
        if prompt_handler.listen_to_keys:
            character = event.char
            gui_handler.print_text(f"USER: {character}\n\n", "white")
            prompt_handler.pressed_key = character
            prompt_handler.key_is_caught= True
    
    def create_start_stop_record_button(self):
        # Create a button that will start or stop the recording
        # Initialize the state to 'start'
        self.record_state = 'start'
        self.record_button = tk.Button(self.root, text="Start Recording🎤", command=self.toggle_record, width=20, height=2, font=("Helvetica", 15), foreground= '#353535', background = "light grey")
        self.record_button.pack(pady=10)
    
    def create_toggle_button(self):
        # Create a variable to hold the state of the toggle button
        self.toggle_state = tk.IntVar()
        self.toggle_state.set(0)  # Set the initial state to unchecked
        
        # Create a toggle button
        toggle_button = ttk.Checkbutton(self.root, text="Direct Code Execution", variable=self.toggle_state, command=lambda: self.toggle_execution())
        toggle_button.pack(pady=10)

    def create_toogle_button_two(self):
        # Create a variable to hold the state of the toggle button
        self.toggle_state_two = tk.IntVar()
        self.toggle_state_two.set(0)  # Set the initial state to unchecked

        # Create a toggle button
        toggle_button_two = ttk.Checkbutton(self.root, text="Follow-Up Questions", variable=self.toggle_state_two, command=lambda: self.toggle_execution_two())
        toggle_button_two.pack(pady=0)
    
    def create_voice_dropdown(self):
        # Create a variable to hold the selected value
        self.voice = tk.StringVar()
        self.voice.set("onyx")

        # Create a dropdown
        voice_dropdown = ttk.OptionMenu(self.root, self.voice, "Voice = Onyx", "Voice = Onyx", "Voice = Alloy", "Voice = Echo", "Voice = Fable", "Voice = Nova", "Voice = Shimmer", command=lambda x: self.change_voice(x))
        voice_dropdown.pack(pady=5)

    def create_text_window(self):
        # Create a Scrollbar
        scrollbar = ttk.Scrollbar(self.root)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a Text widget
        self.text_field = tk.Text(self.root, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.text_field.pack(padx=35, pady=35, fill=tk.BOTH, expand=True)

        self.text_field.tag_config("tag_green", foreground="green")
        self.text_field.tag_config("tag_red", foreground="red")
        self.text_field.tag_config("tag_white", foreground="white")
        self.text_field.tag_config("tag_blue", foreground="blue")
        self.text_field.tag_config("tag_light_blue", foreground="#ADD8E6")

        # make background color of the text field black
        self.text_field.config(background="black")

        # Make the Text widget read-only
        self.text_field.config(state="disabled")

        # Configure the Scrollbar to scroll the Text widget
        scrollbar.config(command=self.text_field.yview)

    def start_gui(self):
        # Start the GUI event loop
        self.root.mainloop()   

# recording user-sound to text and playing ai-text to sound
class SoundHandler:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.voice_agent = "onyx"

    def start_recording(self, name):
        self.is_recording = True
        self.filename = name + ".wav"
        self.chunk = 1024
        self.FORMAT = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.channels,
                                  rate=self.sample_rate,
                                  input=True,
                                  output=True,
                                  frames_per_buffer=self.chunk)
        print("Recording...")

        def record_thread():
            while self.is_recording:
                data = self.stream.read(self.chunk)
                self.frames.append(data)

        threading.Thread(target=record_thread).start()

    def stop_recording(self):
        os.chdir(gui_handler.files_path)
        self.is_recording = False
        print("Recording completed.")
        wf = wave.open(self.filename, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        self.frames = []
        os.chdir(gui_handler.main_path)


    def text_to_speech(text, client, voice_agent):
        # go to file subdirectory
        speech_file_path = gui_handler.files_path + "/generated_audio.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_agent,
            input=text
        )
        response.stream_to_file(speech_file_path)
        gui_handler.play_sound("generated_audio.mp3")
        #os.system("generated_audio.mp3")
    
    def speech_to_text(audio_file_path, client):
        # change directory to subdirectory
        os.chdir(gui_handler.files_path)
        audio_file= open(audio_file_path, "rb")
        transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
        )
        # change directory back to main directory
        os.chdir(gui_handler.main_path)
        return transcript.text

    # listen to the microphone for a given amount of seconds and return the text
    def record_request(seconds, client):
        # take wav file and return text through openai
        def speech_to_text(audio_file_path):
            audio_file= open(audio_file_path, "rb")
            transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
            )
            # print text to gui
            gui_handler.print_text(f"USER: \n{transcript.text}\n\n", "white") 
            return transcript.text
        
        # record the audio from the laptop microphone to wav file
        def record_audio(name, seconds):
            # the file name output you want to record into
            filename = name + ".wav"
            # set the chunk size of 1024 samples
            chunk = 1024
            # sample format
            FORMAT = pyaudio.paInt16
            # mono, change to 2 if you want stereo
            channels = 1
            # 44100 samples per second
            sample_rate = 44100
            record_seconds = seconds
            # initialize PyAudio object
            p = pyaudio.PyAudio()
            # open stream object as input & output
            stream = p.open(format=FORMAT,
                            channels=channels,
                            rate=sample_rate,
                            input=True,
                            output=True,
                            frames_per_buffer=chunk)
            frames = []
            print("Recording...")
            for i in range(int(44100 / chunk * record_seconds)):
                data = stream.read(chunk)
                # if you want to hear your voice while recording
                # stream.write(data)
                frames.append(data)
            # stop and close stream
            stream.stop_stream()
            stream.close()
            # terminate pyaudio object
            p.terminate()
            print("Recording completed.")
            # save audio file
            # open the file in 'write bytes' mode
            wf = wave.open(filename, "wb")
            # set the channels
            wf.setnchannels(channels)
            # set the sample format
            wf.setsampwidth(p.get_sample_size(FORMAT))
            # set the sample rate
            wf.setframerate(sample_rate)
            # write the frames as bytes
            wf.writeframes(b"".join(frames))
            # close the file
            wf.close()


        record_audio("audio_record", seconds)
        return(speech_to_text("audio_record.wav"))

# connection to powershell
class ShellHandler:
    def __init__(self):
        self.shell_process = subprocess.Popen(["powershell", "-Command", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding = 'utf-8')

    def catch_shell_output(self):
        shell_output = ""
        for line in self.shell_process.stdout:
            if line == "IDENTIFIER_251223\n": # search for the identifier to know the end of the output
                break
            shell_output += line
        return shell_output

    def send_shell_commands(self, commands):
        commands += "\necho 'IDENTIFIER_251223'\n" # Identifier is added to the end of the commands to know when to stop reading the output
        commands = "clear\n" + commands
        self.shell_process.stdin.write(commands)
        self.shell_process.stdin.flush()
        return commands

    def save_to_file(self, shell_output, commands, filename):
        os.chdir(gui_handler.log_path)

        # make it utf-8 so that also korean or russian characters can be saved
        with open(filename, "a", encoding="utf-8") as f:
            f.write("commands:\n")
            f.write(commands)
            f.write("\n\noutput:\n")
            f.write(shell_output)
        os.chdir(gui_handler.main_path)

    def execute(self, commands):
        self.send_shell_commands(commands)
        shell_output = self.catch_shell_output()
        self.save_to_file(shell_output, commands, "complete_command_history.txt")

        gui_handler.print_text(f"POWER SHELL: \n{shell_output}\n\n", "red") 

        # count tokens of the power shell answer, also count the letters of power shell answer
        shell_answer_tokens = PromptHandler.num_tokens_from_string(shell_output, 'cl100k_base') #cl100k_base #p50k_base
        shell_answer_letters = len(shell_output)

        # if the answer is too long, the cut it down
        if shell_answer_tokens > 1000:
            # check how many percentage we are too long in terms of tokens, then cut the answer down by that percentage (in terms of letters)
            percentage_too_long = (shell_answer_tokens-1000)/shell_answer_tokens
            shell_output = shell_output[:int(round(shell_answer_letters*(1-percentage_too_long), 0))]
            shell_output += "\n\nSYSTEM INFO: \nPower Shell Answer exceeds 1000 tokens and was thus shortened.\n\n"
            # speak to the user
            gui_handler.print_text(f"SYSTEM INFO: \nPower Shell Answer exceeds 1000 tokens and was thus shortened for the prompt history.\n\n", "light_blue")

        
        PromptHandler.add_to_chat_history(shell_output, "system")

        # save the message stream
        PromptHandler.save_chat_history(prompt_handler.chat_history)

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
        if response_message == prompt_handler.last_ai_response:
            # if so, then reset the chat history
            prompt_handler.chat_history = PromptHandler.reset_chat_history()
            gui_handler.print_text(f"SYSTEM INFO: \nSame AI response as last time, chat history reset.\n\n", "light_blue")

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

# transfer prompts between pipes
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
        os.chdir(gui_handler.files_path)
        with open("pre_prompt_shell.txt", "r") as f:
            preprompt = f.read()
        os.chdir(gui_handler.main_path)
        return preprompt
    
    def get_forwarding_prompt():
        # load the forwarding prompt from the external file
        os.chdir(gui_handler.files_path)
        with open("pre_prompt_forwarder.txt", "r") as f:
            forwarding_prompt = f.read()
        os.chdir(gui_handler.main_path)
        return forwarding_prompt

    def reset_chat_history():

        # reset last ai response
        prompt_handler.last_ai_response = None

        # reset the chat history
        chat_history = [
            {
                "role": "system",
                "content": PromptHandler.get_preprompt()
            }
        ]
        return chat_history
    
    def add_to_chat_history(message, role):
        prompt_handler.chat_history.append({
            "role": role,
            "content": message
        })

    # analyze the response from the llm and check if it is a shell command or a user message
    # we create a second agent that takes care of the forwarding decision
    def forward_by_ai(response_message):
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
        answer_type = OpenAiHandler.generate_forwarding_decision(forwarding_chat_history, openai_handler.OpenAiClient)

        # if the ai response is for the user, print it to the user Interace 
        if answer_type == "user":
            # if string goes like talk_to_user("message"), then clean it
            if response_message.startswith("talk_to_user("):
                clean_message = response_message[14:-2]
            else:
                clean_message = response_message

            PromptHandler.add_to_chat_history(clean_message, "assistant")
            
            gui_handler.print_text(f"AI TO USER: \n{clean_message}\n\n", "white") 

            SoundHandler.text_to_speech(clean_message, openai_handler.OpenAiClient, sound_handler.voice_agent)

            # show the number of tokens used in the current conversation
            token_use = PromptHandler.num_tokens_from_string(str(prompt_handler.chat_history), 'cl100k_base') #cl100k_base #p50k_base
            prompt_handler.current_token_use = token_use
            token_max = 16384
            gui_handler.print_text(f"SYSTEM INFO: \nTokens used: {token_use} / {token_max} ({round(token_use/token_max*100, 2)} %)\n\n", "light_blue")

            # save the message stream (here we are at the end of the conversation)
            PromptHandler.save_chat_history(prompt_handler.chat_history)

            # if there are too many tokens used, then reset the chat history forcefully and let the user know
            if token_use > token_max-2000:
                prompt_handler.chat_history = PromptHandler.reset_chat_history()
                gui_handler.print_text(f"SYSTEM INFO: \nMaximum number of tokens reached, chat history reset.\n\n", "light_blue")
                

        # if the ai response is a command, forward it to the shell handler
        elif answer_type == "shell":
            # check if prompt handler is in "Ask Before Execution" mode
            if prompt_handler.ask_for_execution:
                #gui
                gui_handler.print_text(f"AI PROPOSAL: \n{response_message}\n\n", "green")
                gui_handler.print_text("SYSTEM INFO: \nLet through? (y/n): \n", "light_blue")
                
                # define a function that listens to the keys of the UI, this function is run in a thread
                # It felt clunky and hacky but it works
                def listen_to_keys(response_message = response_message):
                    prompt_handler.listen_to_keys = True
                    prompt_handler.key_is_caught = False
                    while prompt_handler.pressed_key is None and prompt_handler.key_is_caught is False:
                        pass
                    
                    # save the key that was pressed
                    key = prompt_handler.pressed_key
                    prompt_handler.listen_to_keys = False

                    user_decision = key

                    # reset the key-catch-helpers
                    prompt_handler.pressed_key = None
                    prompt_handler.key_is_caught = False
                    prompt_handler.listen_to_keys = False
                    
                    # if y or Y or enter is pressed, then forward the message to the shell
                    if user_decision == "y" or user_decision == "Y" or user_decision == "\r":
                        PromptHandler.add_to_chat_history(response_message, "assistant")
                        shell_handler.execute(response_message)
                        
                        # give power shell answer back to the ai (this could create a loop)
                        response_message = OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)
                    else:
                        gui_handler.print_text("SYSTEM INFO: \nShell execution blocked by user due to security issues.\n\n", "light_blue")
                        PromptHandler.add_to_chat_history(response_message, "assistant")
                        # save the message stream (here we are at the end of the conversation)
                        PromptHandler.save_chat_history(prompt_handler.chat_history)


                # start a thread that listens to the keys
                threading.Thread(target=listen_to_keys).start()

            else:  # if not in ask for execution mode - forward everything to the shell
                gui_handler.print_text(f"AI CODE: \n{response_message}\n\n", "green") 
                PromptHandler.add_to_chat_history(response_message, "assistant")
                shell_handler.execute(response_message)
                
                # give power shell answer back to the ai (this could create a loop)
                response_message = OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)

        elif answer_type == "empty": # if the ai response is none, then do nothing
            gui_handler.print_text(f"SYSTEM INFO: \nModel created empty reply message for the user.\n\n", "light_blue")
        else: # if the ai response is neither, then print a warning
            gui_handler.print_text(f"SYSTEM INFO: \nDebug Warning: The forwarding decision is neither 'shell' nor 'user' but {answer_type}.\n\n", "light_blue")

    
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

def main():
    
    # define the GUI
    global gui_handler
    gui_handler = GuiHandler()

    # start connection to the powershell
    global shell_handler
    shell_handler = ShellHandler()

    # start connection to the openai api
    global openai_handler
    openai_handler = OpenAiHandler()

    # start the prompt handler
    global prompt_handler
    prompt_handler = PromptHandler()

    # start the sound handler
    global sound_handler
    sound_handler = SoundHandler()

    # start the gui
    gui_handler.start_gui()

if __name__ == '__main__':
    main()