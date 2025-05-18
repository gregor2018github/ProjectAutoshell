"""Manages the Autoshell graphical user interface, including user input, output display, and interaction controls."""

import os
import tkinter as tk
from tkinter import PhotoImage, ttk
from pygame import mixer
import app_globals
from sound_handler import SoundHandler
from openai_handler import OpenAiHandler
from prompt_handler import PromptHandler
   
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
        self.text_field.insert(tk.END, text, f"tag_{color}")
        
        # refresh the text field
        self.text_field.update_idletasks()
        self.text_field.see(tk.END)

        # remove reactivity of the text field so that the user can not edit it
        self.text_field.config(state="disabled")

    def toggle_record(self):
        # Toggle the recording state
        if self.record_state == 'start':
            if self.start_record():  # Check if recording started successfully
                self.record_button.config(text="Stop Recording 🎤")
                self.record_state = 'stop'
            # Else, start_record failed; button and state remain 'start'. 
            # Error message would have been printed by SoundHandler.
        else:
            self.stop_record()
            self.record_button.config(text="Start Recording 🎤")
            self.record_state = 'start'

    def start_record(self):
        # Start recording
        return app_globals.sound_handler_object.start_recording("audio_record")
    
    def stop_record(self):
        # Stop recording
        app_globals.sound_handler_object.stop_recording()

        # if follow up questions are enabled, then do not reset the chat history
        if not app_globals.prompt_handler_object.follow_up_questions:
            app_globals.prompt_handler_object.chat_history = PromptHandler.reset_chat_history()

        # use speech to text method to get the text from the recorded audio
        user_input = SoundHandler.speech_to_text("audio_record.wav", app_globals.openai_handler_object.OpenAiClient)

        # print user input to gui, then generate ai response
        self.print_text(f"USER: \n{user_input}\n\n", "white")
        PromptHandler.add_to_chat_history(user_input, "user")
        OpenAiHandler.generate_AI_response(app_globals.prompt_handler_object.chat_history, app_globals.openai_handler_object.OpenAiClient)

    def toggle_execution(self):
        # Toggle the execution mode
        if self.toggle_state.get() == 1:
            app_globals.prompt_handler_object.ask_for_execution = False
            self.print_text("SYSTEM INFO: \nDirect Code Execution Enabled\n\n", "light_blue")
        else:
            app_globals.prompt_handler_object.ask_for_execution = True
            self.print_text("SYSTEM INFO: \nDirect Code Execution Disabled\n\n", "light_blue")
    
    def toggle_execution_two(self):
        # toggle follow up question mode
        if self.toggle_state_two.get() == 1:
            app_globals.prompt_handler_object.follow_up_questions = True
            self.print_text("SYSTEM INFO: \nFollow-Up Questions Enabled\n\n", "light_blue")
        else:
            app_globals.prompt_handler_object.follow_up_questions = False
            self.print_text("SYSTEM INFO: \nFollow-Up Questions Disabled\n\n", "light_blue")        

    def change_voice(self, voice):
        # Extract voice name from selection (remove "Voice = " prefix)
        voice_name = voice.split("= ")[1].lower() if "= " in voice else voice.lower()
        
        # Change the voice of the AI
        app_globals.sound_handler_object.voice_agent = voice_name
        
        # Display confirmation message
        self.print_text(f"SYSTEM INFO: \nVoice changed to {voice_name.capitalize()}.\n\n", "light_blue")
        
        # Play a sample sound
        os.chdir(self.files_path)
        self.play_sound(f"example_{voice_name}.mp3")
        os.chdir(self.main_path)

    # define what happens when a key is pressed
    def key_pressed(self, event):
        if app_globals.prompt_handler_object.listen_to_keys:
            character = event.char
            self.print_text(f"USER: {character}\n\n", "white")
            app_globals.prompt_handler_object.pressed_key = character
            app_globals.prompt_handler_object.key_is_caught= True
    
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

    # define what happens when a key is pressed
    def key_pressed(self, event):
        if app_globals.prompt_handler_object.listen_to_keys:
            character = event.char
            self.print_text(f"USER: {character}\n\n", "white")
            app_globals.prompt_handler_object.pressed_key = character
            app_globals.prompt_handler_object.key_is_caught= True
    
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
