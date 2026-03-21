#-------------------------------------------------------
# Imports
#-------------------------------------------------------

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

#-------------------------------------------------------
# Constants and Global Variables
#-------------------------------------------------------

# UI Stuff
BACKGROUND_IMAGE = "background_image2.png"
TEXT_COLOR_USER = "white"
TEXT_COLOR_SETTINGS = "light_blue"
TEXT_COLOR_POWER_SHELL = "red"
TEXT_COLOR_AI = "white"
TEXT_COLOR_AI_PROPOSAL = "green"

# Sound Stuff
SOUND_CHUNK = 1024
SOUND_CHANNELS = 1
SOUND_SAMPLE_RATE = 44100
TTS_MODEL = "tts-1"
SPEECH_TO_TEXT_MODEL = "whisper-1"

# Shell Stuff
MAX_TOKENS_SHELL_ANSWER = 1000

# OpenAI Stuff
OPEN_AI_API_KEY_ENV_VARIABLE = "OPENAI_API_KEY"
LARGE_LANGUAGE_MODEL = "gpt-5.4-nano" # "gpt-3.5-turbo-16k", "gpt-5-mini", "gpt-realtime"
MODEL_TEMPERATURE = 1 # 1.1 with gpt-3.5-turbo-16k
MODEL_MAX_TOKENS = 1000
MODEL_TOP_P = 1
MODEL_FREQUENCY_PENALTY = 0
MODEL_PRESENCE_PENALTY = 0
LARGE_LANGUAGE_MODEL_FOR_FORWARDING_DECISION = "gpt-5.4-nano" # "gpt-3.5-turbo", "gpt-realtime"
FORWARDING_MODEL_TEMPERATURE = 1 # 0.5 with gpt-3.5-turbo
FORWARDING_MODEL_MAX_TOKENS = 5
FORWARDING_MODEL_TOP_P = 1
FORWARDING_MODEL_FREQUENCY_PENALTY = 0
FORWARDING_MODEL_PRESENCE_PENALTY = 0


#-------------------------------------------------------
# Guided User Interface
#-------------------------------------------------------

class GuiHandler:
    def __init__(self):
        # Initialize the mixer module for playing sound
        mixer.init()
        
        # Create the main window
        root = tk.Tk()
        root.title("Autoshell")
        
        # Configure modern styling
        self.setup_modern_style(root)
        # check the size of the current screen
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        # make the window cover the whole screen
        root.geometry("%dx%d" % (round(width/2,0), round(height/2,0)))

        # load it into the class
        self.root = root

        # Load the image file
        # file path is current path + /files + /background_image.png
        picture_path = os.path.join(os.getcwd(), "files", BACKGROUND_IMAGE)
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
        self.create_input_mode_radio_buttons()
        self.create_voice_dropdown()
        self.create_debug_toggle_button()
        self.create_text_window()
        self.create_debug_panel()

        # Keyboard input mode variables
        self.keyboard_input_mode = False
        self.keyboard_input_buffer = ""

        # create two paths, the main path and the subdirectory path for files
        self.main_path = os.getcwd()
        self.files_path = os.path.join(self.main_path, "files")
        self.log_path = os.path.join(self.main_path, "logs")

        # bind the key listening function to the gui
        self.root.bind("<Key>", self.key_pressed)
    
    def setup_modern_style(self, root):
        """Configure modern flat styling for ttk widgets"""
        style = ttk.Style(root)
        
        # Use clam theme as base (more customizable)
        style.theme_use('clam')
        
        # Modern color palette
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#e0e0e0',
            'accent': '#4a9eff',
            'accent_hover': '#6bb3ff',
            'button_bg': '#3d3d3d',
            'button_hover': '#4a4a4a',
            'checkbox_bg': '#363636',
        }
        
        # Style for Checkbuttons (toggle buttons)
        style.configure('Modern.TCheckbutton',
            background='#c0c0c0',
            foreground='#1a1a1a',
            font=('Segoe UI', 10),
            padding=(10, 8),
            focuscolor='none'
        )
        style.map('Modern.TCheckbutton',
            background=[('active', '#d0d0d0'), ('selected', '#c0c0c0')],
            foreground=[('active', '#1a1a1a'), ('selected', '#1a1a1a')]
        )
        
        # Style for Radiobuttons
        style.configure('Modern.TRadiobutton',
            background='#c0c0c0',
            foreground='#1a1a1a',
            font=('Segoe UI', 10),
            padding=(10, 8),
            focuscolor='none'
        )
        style.map('Modern.TRadiobutton',
            background=[('active', '#d0d0d0'), ('selected', '#c0c0c0')],
            foreground=[('active', '#1a1a1a'), ('selected', '#1a1a1a')]
        )
        
        # Style for OptionMenu (dropdown)
        style.configure('Modern.TMenubutton',
            background='#3d3d3d',
            foreground='#e0e0e0',
            font=('Segoe UI', 10),
            padding=(12, 8),
            borderwidth=0,
            relief='flat',
            arrowcolor='#e0e0e0'
        )
        style.map('Modern.TMenubutton',
            background=[('active', '#4a4a4a')],
            foreground=[('active', '#ffffff')]
        )
        
        # Style for Scrollbar
        style.configure('Modern.Vertical.TScrollbar',
            background='#3d3d3d',
            troughcolor='#2b2b2b',
            borderwidth=0,
            arrowcolor='#808080'
        )

    def play_sound(self, file_name):
        self.debug_log("Playing audio...")
        t = time.time()
        full_path = os.path.join(self.files_path, file_name)
        dummy_path = os.path.join(self.files_path, "audio_dummy.wav")
        mixer.music.load(full_path)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)
        # load a dummy file so that the "generated_audio.mp3" can be overwritten and be used again
        mixer.music.load(dummy_path)
        self.debug_log(f"Audio playback done ({time.time()-t:.2f}s)")
    
    def print_text(self, text, color):
        # If called from a background thread, reschedule on the main thread
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.print_text, text, color)
            return

        self.text_field.config(state="normal")
        self.text_field.insert(tk.END, text, f"tag_{color}")
        
        # refresh the text field
        self.text_field.update_idletasks()
        self.text_field.see(tk.END)

        # remove reactivity of the text field so that the user can not edit it
        self.text_field.config(state="disabled")

    def toggle_record(self):
        # Check if keyboard input mode is enabled
        if self.input_mode.get() == "keyboard":
            # Start keyboard input mode
            if not self.keyboard_input_mode:
                self.start_keyboard_input()
            return
        
        # Toggle the recording state (microphone mode)
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
        return sound_handler.start_recording("audio_record")
    
    def stop_record(self):
        # Stop recording
        sound_handler.stop_recording()

        # if follow up questions are enabled, then do not reset the chat history
        if not prompt_handler.follow_up_questions:
            prompt_handler.chat_history = PromptHandler.reset_chat_history()

        # Disable button and run pipeline on background thread
        self.record_button.config(state="disabled")
        threading.Thread(target=self._run_pipeline, kwargs={"from_speech": True}, daemon=True).start()

    def start_keyboard_input(self):
        """Start keyboard input mode - allows user to type their message"""
        self.keyboard_input_mode = True
        self.keyboard_input_buffer = ""
        self.record_button.config(text="Type & Press Enter ⌨️")
        
        # Enable the text field for input
        self.text_field.config(state="normal")
        self.text_field.insert(tk.END, "YOUR INPUT: \n", "tag_white")
        self.text_field.see(tk.END)
        
        # Store the position where user input starts
        self.keyboard_input_start = self.text_field.index(tk.END)
        
        # Set focus to text field to capture all key events
        self.text_field.focus_set()
        
        # Bind keyboard events for typing - bind to text_field directly
        self.text_field.bind("<Key>", self.handle_keyboard_input)
        # Also bind space explicitly to prevent checkbox toggling
        self.text_field.bind("<space>", self.handle_keyboard_input)
    
    def handle_keyboard_input(self, event):
        """Handle keyboard input when in keyboard input mode"""
        # If not in keyboard input mode but listen_to_keys is active (for y/n prompts), use the original handler
        if not self.keyboard_input_mode:
            if prompt_handler.listen_to_keys:
                character = event.char
                gui_handler.print_text(f"USER: {character}\n\n", TEXT_COLOR_USER)
                prompt_handler.pressed_key = character
                prompt_handler.key_is_caught = True
            return
        
        # Handle Enter key to submit input
        if event.keysym == "Return":
            self.submit_keyboard_input()
            return "break"
        
        # Handle Backspace
        if event.keysym == "BackSpace":
            if self.keyboard_input_buffer:
                self.keyboard_input_buffer = self.keyboard_input_buffer[:-1]
                # Remove last character from text field
                self.text_field.delete("end-2c", "end-1c")
            return "break"
        
        # Handle Escape to cancel
        if event.keysym == "Escape":
            self.cancel_keyboard_input()
            return "break"
        
        # Handle space key explicitly
        if event.keysym == "space":
            self.keyboard_input_buffer += " "
            self.text_field.insert(tk.END, " ", "tag_white")
            self.text_field.see(tk.END)
            return "break"
        
        # Handle regular character input (excluding special keys)
        if event.char and event.char.isprintable() and len(event.char) == 1:
            self.keyboard_input_buffer += event.char
            self.text_field.insert(tk.END, event.char, "tag_white")
            self.text_field.see(tk.END)
            return "break"
        
        return "break"
    
    def submit_keyboard_input(self):
        """Submit the keyboard input and process it like voice input"""
        user_input = self.keyboard_input_buffer.strip()
        
        # Reset keyboard input mode
        self.keyboard_input_mode = False
        self.keyboard_input_buffer = ""
        self.record_button.config(text="Start Recording 🎤")
        
        # Unbind keyboard events from text field
        self.text_field.unbind("<Key>")
        self.text_field.unbind("<space>")
        
        # Disable text field editing
        self.text_field.config(state="normal")
        self.text_field.insert(tk.END, "\n\n", "tag_white")
        self.text_field.config(state="disabled")
        
        # Rebind original key handler to root
        self.root.bind("<Key>", self.key_pressed)
        # Return focus to root
        self.root.focus_set()
        
        if not user_input:
            gui_handler.print_text("SYSTEM INFO: \nEmpty input, please try again.\n\n", TEXT_COLOR_SETTINGS)
            return

        # if follow up questions are enabled, then do not reset the chat history
        if not prompt_handler.follow_up_questions:
            prompt_handler.chat_history = PromptHandler.reset_chat_history()

        # Disable button and run pipeline on background thread
        self.record_button.config(state="disabled")
        threading.Thread(target=self._run_pipeline, args=(user_input,), daemon=True).start()
    
    def cancel_keyboard_input(self):
        """Cancel keyboard input mode"""
        self.keyboard_input_mode = False
        self.keyboard_input_buffer = ""
        self.record_button.config(text="Start Recording 🎤")
        
        # Unbind keyboard events from text field
        self.text_field.unbind("<Key>")
        self.text_field.unbind("<space>")
        
        # Disable text field editing and add cancellation message
        self.text_field.config(state="normal")
        self.text_field.insert(tk.END, "\n[Cancelled]\n\n", "tag_light_blue")
        self.text_field.config(state="disabled")
        
        # Rebind original key handler to root
        self.root.bind("<Key>", self.key_pressed)
        # Return focus to root
        self.root.focus_set()
        
        gui_handler.print_text("SYSTEM INFO: \nKeyboard input cancelled.\n\n", TEXT_COLOR_SETTINGS)

    def toggle_execution(self):
        # Toggle the execution mode
        if self.toggle_state.get() == 1:
            prompt_handler.ask_for_execution = False
            gui_handler.print_text("SYSTEM INFO: \nDirect Code Execution Enabled\n\n", TEXT_COLOR_SETTINGS)
        else:
            prompt_handler.ask_for_execution = True
            gui_handler.print_text("SYSTEM INFO: \nDirect Code Execution Disabled\n\n", TEXT_COLOR_SETTINGS)
    
    def toggle_execution_two(self):
        # toggle follow up question mode
        if self.toggle_state_two.get() == 1:
            prompt_handler.follow_up_questions = True
            gui_handler.print_text("SYSTEM INFO: \nFollow-Up Questions Enabled\n\n", TEXT_COLOR_SETTINGS)
        else:
            prompt_handler.follow_up_questions = False
            gui_handler.print_text("SYSTEM INFO: \nFollow-Up Questions Disabled\n\n", TEXT_COLOR_SETTINGS)        

    def change_input_mode(self):
        # Handle input mode change between keyboard and microphone
        if self.input_mode.get() == "keyboard":
            # Change button text to reflect keyboard mode
            self.record_button.config(text="Start Typing ⌨️")
            gui_handler.print_text("SYSTEM INFO: \nInput Mode: Keyboard - Type your message and press Enter\n\n", TEXT_COLOR_SETTINGS)
        else:  # microphone mode
            # If keyboard input mode was active, cancel it properly
            if self.keyboard_input_mode:
                self.keyboard_input_mode = False
                self.keyboard_input_buffer = ""
                self.record_button.config(text="Start Recording 🎤")
                
                # Unbind keyboard events from text field
                self.text_field.unbind("<Key>")
                self.text_field.unbind("<space>")
                
                # Disable text field editing and add cancellation message
                self.text_field.config(state="normal")
                self.text_field.insert(tk.END, "\n[Switched to Microphone mode]\n\n", "tag_light_blue")
                self.text_field.config(state="disabled")
                
                # Rebind original key handler to root
                self.root.bind("<Key>", self.key_pressed)
                # Return focus to root
                self.root.focus_set()
            else:
                # Change button text back to microphone mode
                self.record_button.config(text="Start Recording 🎤")
            
            gui_handler.print_text("SYSTEM INFO: \nInput Mode: Microphone\n\n", TEXT_COLOR_SETTINGS)

    def change_voice(self, voice):
        # Extract voice name from selection (remove "Voice = " prefix)
        voice_name = voice.split("= ")[1].lower() if "= " in voice else voice.lower()
        
        # Change the voice of the AI
        sound_handler.voice_agent = voice_name
        
        # Display confirmation message
        gui_handler.print_text(f"SYSTEM INFO: \nVoice changed to {voice_name.capitalize()}.\n\n", TEXT_COLOR_SETTINGS)
        
        # Play a sample sound
        gui_handler.play_sound(f"example_{voice_name}.mp3")

    # define what happens when a key is pressed
    def key_pressed(self, event):
        if prompt_handler.listen_to_keys:
            character = event.char
            gui_handler.print_text(f"USER: {character}\n\n", TEXT_COLOR_USER)
            prompt_handler.pressed_key = character
            prompt_handler.key_is_caught= True
    
    def create_start_stop_record_button(self):
        # Create a button that will start or stop the recording
        # Initialize the state to 'start'
        self.record_state = 'start'
        self.record_button = tk.Button(
            self.root, 
            text="Start Recording 🎤", 
            command=self.toggle_record, 
            width=18, 
            height=1,
            font=("Segoe UI", 13, "bold"),
            foreground='#ffffff',
            background='#4a9eff',
            activeforeground='#ffffff',
            activebackground='#6bb3ff',
            relief='flat',
            cursor='hand2',
            bd=0,
            highlightthickness=0,
            padx=20,
            pady=12
        )
        self.record_button.pack(pady=20)
        
        # Add hover effects
        self.record_button.bind('<Enter>', lambda e: self.record_button.config(background='#6bb3ff'))
        self.record_button.bind('<Leave>', lambda e: self.record_button.config(background='#4a9eff'))
    
    def create_toggle_button(self):
        # Create a variable to hold the state of the toggle button
        self.toggle_state = tk.IntVar()
        self.toggle_state.set(0)  # Set the initial state to unchecked
        
        # Create a toggle button with modern style
        toggle_button = ttk.Checkbutton(
            self.root, 
            text="Direct Code Execution", 
            variable=self.toggle_state, 
            command=lambda: self.toggle_execution(),
            style='Modern.TCheckbutton'
        )
        toggle_button.pack(pady=6)

    def create_toogle_button_two(self):
        # Create a variable to hold the state of the toggle button
        self.toggle_state_two = tk.IntVar()
        self.toggle_state_two.set(0)  # Set the initial state to unchecked

        # Create a toggle button with modern style
        toggle_button_two = ttk.Checkbutton(
            self.root, 
            text="Follow-Up Questions", 
            variable=self.toggle_state_two, 
            command=lambda: self.toggle_execution_two(),
            style='Modern.TCheckbutton'
        )
        toggle_button_two.pack(pady=6)
    
    def create_input_mode_radio_buttons(self):
        # Create a variable to hold the input mode selection
        self.input_mode = tk.StringVar()
        self.input_mode.set("microphone")  # Set default to microphone

        # Create a frame to hold the radio buttons (transparent background)
        radio_frame = tk.Frame(self.root)
        radio_frame.pack(pady=6)
        
        # Add label for the radio button group
        mode_label = tk.Label(
            radio_frame,
            text="Input Mode:",
            font=("Segoe UI", 10, "bold"),
            foreground='#000000'
        )
        mode_label.pack(side=tk.LEFT, padx=(0, 10))

        # Create radio button for Microphone
        microphone_radio = ttk.Radiobutton(
            radio_frame,
            text="🎤 Microphone",
            variable=self.input_mode,
            value="microphone",
            command=self.change_input_mode,
            style='Modern.TRadiobutton'
        )
        microphone_radio.pack(side=tk.LEFT, padx=5)

        # Create radio button for Keyboard
        keyboard_radio = ttk.Radiobutton(
            radio_frame,
            text="⌨️ Keyboard",
            variable=self.input_mode,
            value="keyboard",
            command=self.change_input_mode,
            style='Modern.TRadiobutton'
        )
        keyboard_radio.pack(side=tk.LEFT, padx=5)

    def create_voice_dropdown(self):
        # Create a variable to hold the selected value
        self.voice = tk.StringVar()
        self.voice.set("onyx")

        # Create a dropdown with modern style
        voice_dropdown = ttk.OptionMenu(
            self.root, 
            self.voice, 
            "Voice = Onyx", 
            "Voice = Onyx", 
            "Voice = Alloy", 
            "Voice = Echo", 
            "Voice = Fable", 
            "Voice = Nova", 
            "Voice = Shimmer", 
            command=lambda x: self.change_voice(x),
            style='Modern.TMenubutton'
        )
        voice_dropdown.pack(pady=12)

    def create_text_window(self):
        # Create a Scrollbar with modern style
        scrollbar = ttk.Scrollbar(self.root, style='Modern.Vertical.TScrollbar')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=20)

        # Create a Text widget with modern styling
        self.text_field = tk.Text(
            self.root, 
            wrap=tk.WORD, 
            yscrollcommand=scrollbar.set,
            font=('Consolas', 11),
            relief='flat',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#3d3d3d',
            highlightcolor='#4a9eff',
            insertbackground='#ffffff',
            selectbackground='#4a9eff',
            selectforeground='#ffffff'
        )
        self.text_field.pack(padx=25, pady=(15, 25), fill=tk.BOTH, expand=True)

        # Configure text colors with modern palette
        self.text_field.tag_config("tag_green", foreground="#50fa7b")
        self.text_field.tag_config("tag_red", foreground="#ff5555")
        self.text_field.tag_config("tag_white", foreground="#f8f8f2")
        self.text_field.tag_config("tag_blue", foreground="#8be9fd")
        self.text_field.tag_config("tag_light_blue", foreground="#8be9fd")

        # Modern dark background for the text field
        self.text_field.config(background="#1e1e1e")

        # Make the Text widget read-only
        self.text_field.config(state="disabled")

        # Configure the Scrollbar to scroll the Text widget
        scrollbar.config(command=self.text_field.yview)

    # ----- Debug Panel -----

    def create_debug_toggle_button(self):
        self.debug_toggle_state = tk.IntVar()
        self.debug_toggle_state.set(0)

        toggle_button = ttk.Checkbutton(
            self.root,
            text="Debug Panel",
            variable=self.debug_toggle_state,
            command=self.toggle_debug_panel,
            style='Modern.TCheckbutton'
        )
        toggle_button.pack(pady=6)

    def create_debug_panel(self):
        self.debug_frame = tk.Frame(self.root, height=150)
        self.debug_scrollbar = ttk.Scrollbar(self.debug_frame, style='Modern.Vertical.TScrollbar')
        self.debug_text = tk.Text(
            self.debug_frame,
            wrap=tk.WORD,
            yscrollcommand=self.debug_scrollbar.set,
            font=('Consolas', 9),
            relief='flat',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground='#3d3d3d',
            highlightcolor='#ffa500',
            background='#1a1a2e',
            foreground='#ffa500',
            insertbackground='#ffa500',
            state='disabled'
        )
        self.debug_scrollbar.config(command=self.debug_text.yview)
        self.debug_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Panel starts hidden
        self.debug_panel_visible = False

    def toggle_debug_panel(self):
        if self.debug_toggle_state.get() == 1:
            self.debug_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=25, pady=(0, 10))
            self.debug_panel_visible = True
        else:
            self.debug_frame.pack_forget()
            self.debug_panel_visible = False

    def debug_log(self, message):
        """Thread-safe: schedules the actual write on the main thread."""
        self.root.after(0, self._debug_log_impl, message)

    def _debug_log_impl(self, message):
        t = time.time()
        ms = int((t % 1) * 1000)
        timestamp = time.strftime("%H:%M:%S") + f".{ms:03d}"
        line = f"[{timestamp}] {message}\n"
        self.debug_text.config(state='normal')
        self.debug_text.insert(tk.END, line)
        self.debug_text.see(tk.END)
        self.debug_text.config(state='disabled')

    # ----- Pipeline (runs on background thread) -----

    def _run_pipeline(self, user_input=None, from_speech=False):
        """Runs the full request pipeline off the main thread."""
        pipeline_start = time.time()
        try:
            self.debug_log("Pipeline started")

            if from_speech:
                user_input = SoundHandler.speech_to_text("audio_record.wav", openai_handler.OpenAiClient)

            self.print_text(f"USER: \n{user_input}\n\n", TEXT_COLOR_USER)
            PromptHandler.add_to_chat_history(user_input, "user")

            OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)

            self.debug_log(f"Pipeline finished. Total: {time.time()-pipeline_start:.2f}s")
        except Exception as e:
            self.debug_log(f"ERROR: {e}")
            self.print_text(f"SYSTEM ERROR: \n{e}\n\n", TEXT_COLOR_POWER_SHELL)
        finally:
            self.root.after(0, self._pipeline_finished)

    def _pipeline_finished(self):
        self.record_button.config(state="normal")

    def start_gui(self):
        # Start the GUI event loop
        self.root.mainloop()

#-------------------------------------------------------
# Recording user-sound to text and playing ai-text to sound
#-------------------------------------------------------

class SoundHandler:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.voice_agent = "onyx"

    def start_recording(self, name)->bool:
        """Start recording audio from the microphone and save it to a file. Returns True if successful, False otherwise."""
        self.is_recording = True
        self.filename = name + ".wav"
        self.chunk = SOUND_CHUNK
        self.FORMAT = pyaudio.paInt16
        self.channels = SOUND_CHANNELS
        self.sample_rate = SOUND_SAMPLE_RATE
        self.p = pyaudio.PyAudio()
        
        try:
            # Only use input mode for recording
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,  # Only need input for recording
                output=False,  # Don't use output during recording
                frames_per_buffer=self.chunk)
            
            print("Recording...")
    
            def record_thread():
                self.frames = []  # Reset frames list
                while self.is_recording:
                    try:
                        data = self.stream.read(self.chunk, exception_on_overflow=False)
                        self.frames.append(data)
                    except Exception as e:
                        print(f"Error in recording thread: {str(e)}")
                        break
            
            threading.Thread(target=record_thread).start()
            return True  # Recording started successfully
        
        except Exception as e:
            self.is_recording = False
            self.p.terminate()
            error_message = f"Could not start recording: {str(e)}\n\n"
            print(error_message)
            gui_handler.print_text(error_message, "red")
            return False  # Failed to start recording

    def stop_recording(self):
        self.is_recording = False
        print("Recording completed.")
        full_path = os.path.join(gui_handler.files_path, self.filename)
        wf = wave.open(full_path, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        self.frames = []


    def text_to_speech(text, client, voice_agent):
        gui_handler.debug_log("Text-to-speech (TTS API)...")
        t = time.time()
        speech_file_path = gui_handler.files_path + "/generated_audio.mp3"
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=voice_agent,
            input=text
        )
        response.stream_to_file(speech_file_path)
        gui_handler.debug_log(f"Text-to-speech done ({time.time()-t:.2f}s)")
        gui_handler.play_sound("generated_audio.mp3")
        #os.system("generated_audio.mp3")
    
    def speech_to_text(audio_file_path, client):
        gui_handler.debug_log("Speech-to-text (Whisper API)...")
        t = time.time()
        full_path = os.path.join(gui_handler.files_path, audio_file_path)
        audio_file = open(full_path, "rb")
        transcript = client.audio.transcriptions.create(
            model=SPEECH_TO_TEXT_MODEL,
            file=audio_file
        )
        gui_handler.debug_log(f"Speech-to-text done ({time.time()-t:.2f}s)")
        return transcript.text

    # listen to the microphone for a given amount of seconds and return the text
    def record_request(seconds, client):
        # take wav file and return text through openai
        def speech_to_text(audio_file_path):
            audio_file= open(audio_file_path, "rb")
            transcript = client.audio.transcriptions.create(
            model=SPEECH_TO_TEXT_MODEL, 
            file=audio_file
            )
            # print text to gui
            gui_handler.print_text(f"USER: \n{transcript.text}\n\n", TEXT_COLOR_USER) 
            return transcript.text
        
        # record the audio from the laptop microphone to wav file
        def record_audio(name, seconds):
            filename = name + ".wav"
            chunk = SOUND_CHUNK
            FORMAT = pyaudio.paInt16
            channels = SOUND_CHANNELS
            sample_rate = SOUND_SAMPLE_RATE
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
            for i in range(int(sample_rate / chunk * record_seconds)):
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

#-------------------------------------------------------
# Connection to PowerShell
#-------------------------------------------------------

class ShellHandler:
    def __init__(self):
        # Use common PowerShell locations or search in PATH
        powershell_paths = [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            r"C:\Windows\System32\powershell.exe",
            "powershell"  # Will use PATH as fallback
        ]
        
        powershell_exe = None
        for path in powershell_paths:
            try:
                # Test if we can start PowerShell with this path
                subprocess.run([path, "-Command", "exit"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               check=False)
                powershell_exe = path
                break
            except FileNotFoundError:
                continue
        
        if not powershell_exe:
            raise FileNotFoundError("Could not find PowerShell executable. Please ensure PowerShell is installed.")
        
        self.shell_process = subprocess.Popen(
            [powershell_exe, "-Command", "-"], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            text=True, 
            encoding='utf-8'
        )

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
        # ensure logs directory exists
        os.makedirs(gui_handler.log_path, exist_ok=True)
        file_path = os.path.join(gui_handler.log_path, filename)

        # make it utf-8 so that also korean or russian characters can be saved
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("commands:\n")
            f.write(commands)
            f.write("\n\noutput:\n")
            f.write(shell_output)

    def execute(self, commands):
        gui_handler.debug_log("Shell execution...")
        t = time.time()
        self.send_shell_commands(commands)
        shell_output = self.catch_shell_output()
        gui_handler.debug_log(f"Shell execution done ({time.time()-t:.2f}s)")
        self.save_to_file(shell_output, commands, "complete_command_history.txt")

        gui_handler.print_text(f"POWER SHELL: \n{shell_output}\n\n", TEXT_COLOR_POWER_SHELL) 

        # count tokens of the power shell answer, also count the letters of power shell answer
        shell_answer_tokens = PromptHandler.num_tokens_from_string(shell_output, 'cl100k_base') #cl100k_base #p50k_base
        shell_answer_letters = len(shell_output)

        # if the answer is too long, the cut it down
        if shell_answer_tokens > MAX_TOKENS_SHELL_ANSWER:
            # check how many percentage we are too long in terms of tokens, then cut the answer down by that percentage (in terms of letters)
            percentage_too_long = (shell_answer_tokens-MAX_TOKENS_SHELL_ANSWER)/shell_answer_tokens
            shell_output = shell_output[:int(round(shell_answer_letters*(1-percentage_too_long), 0))]
            shell_output += f"\n\nSYSTEM INFO: \nPower Shell Answer exceeds {MAX_TOKENS_SHELL_ANSWER} tokens and was thus shortened.\n\n"
            # speak to the user
            gui_handler.print_text(f"SYSTEM INFO: \nPower Shell Answer exceeds {MAX_TOKENS_SHELL_ANSWER} tokens and was thus shortened for the prompt history.\n\n", TEXT_COLOR_SETTINGS)

        
        PromptHandler.add_to_chat_history(shell_output, "system")

        # save the message stream
        PromptHandler.save_chat_history(prompt_handler.chat_history)

#-------------------------------------------------------
# Connection to Open AI API
#-------------------------------------------------------

class OpenAiHandler:

    def __init__(self):
        self.OpenAiClient = OpenAI(
            api_key=os.environ[OPEN_AI_API_KEY_ENV_VARIABLE],
        )

    def generate_AI_response(chat_history, client):
        gui_handler.debug_log(f"Chat completions ({LARGE_LANGUAGE_MODEL})...")
        t = time.time()
        response = client.chat.completions.create(
            model=LARGE_LANGUAGE_MODEL,
            messages=chat_history
        )

        response_message = response.choices[0].message.content
        gui_handler.debug_log(f"Chat completions done ({time.time()-t:.2f}s)") 

        # check if the response is the same as the last one
        if response_message == prompt_handler.last_ai_response:
            # if so, then reset the chat history
            prompt_handler.chat_history = PromptHandler.reset_chat_history()
            gui_handler.print_text(f"SYSTEM INFO: \nSame AI response as last time, chat history reset.\n\n", TEXT_COLOR_SETTINGS)

        # check if message needs to be forwarded to the user or to the shell
        PromptHandler.forward_by_ai(response_message)

    def generate_forwarding_decision(forwarding_chat_history, client):
        gui_handler.debug_log(f"Forwarding decision ({LARGE_LANGUAGE_MODEL_FOR_FORWARDING_DECISION})...")
        t = time.time()
        response = client.chat.completions.create(
            model=LARGE_LANGUAGE_MODEL_FOR_FORWARDING_DECISION,
            messages=forwarding_chat_history
        )

        response_message = response.choices[0].message.content
        gui_handler.debug_log(f"Forwarding decision = \"{response_message}\" ({time.time()-t:.2f}s)")
        return response_message

#-------------------------------------------------------
# Transfer prompts between pipes
#-------------------------------------------------------

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
        full_path = os.path.join(gui_handler.files_path, "pre_prompt_shell.txt")
        with open(full_path, "r") as f:
            preprompt = f.read()
        return preprompt

    def get_forwarding_prompt():
        full_path = os.path.join(gui_handler.files_path, "pre_prompt_forwarder.txt")
        with open(full_path, "r") as f:
            forwarding_prompt = f.read()
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
            
            gui_handler.print_text(f"AI TO USER: \n{clean_message}\n\n", TEXT_COLOR_AI) 

            SoundHandler.text_to_speech(clean_message, openai_handler.OpenAiClient, sound_handler.voice_agent)

            # show the number of tokens used in the current conversation
            token_use = PromptHandler.num_tokens_from_string(str(prompt_handler.chat_history), 'cl100k_base') #cl100k_base #p50k_base
            prompt_handler.current_token_use = token_use
            token_max = 16384
            gui_handler.print_text(f"SYSTEM INFO: \nTokens used: {token_use} / {token_max} ({round(token_use/token_max*100, 2)} %)\n\n", TEXT_COLOR_SETTINGS)

            # save the message stream (here we are at the end of the conversation)
            PromptHandler.save_chat_history(prompt_handler.chat_history)

            # if there are too many tokens used, then reset the chat history forcefully and let the user know
            if token_use > token_max-2000:
                prompt_handler.chat_history = PromptHandler.reset_chat_history()
                gui_handler.print_text(f"SYSTEM INFO: \nMaximum number of tokens reached, chat history reset.\n\n", TEXT_COLOR_SETTINGS)
                

        # if the ai response is a command, forward it to the shell handler
        elif answer_type == "shell":
            # check if prompt handler is in "Ask Before Execution" mode
            if prompt_handler.ask_for_execution:
                #gui
                gui_handler.print_text(f"AI PROPOSAL: \n{response_message}\n\n", TEXT_COLOR_AI_PROPOSAL)
                gui_handler.print_text("SYSTEM INFO: \nLet through? (y/n): \n", TEXT_COLOR_SETTINGS)
                
                # Wait for user key press (already on background thread, so this won't freeze the UI)
                gui_handler.debug_log("Waiting for user approval (y/n)...")
                prompt_handler.listen_to_keys = True
                prompt_handler.key_is_caught = False
                while prompt_handler.pressed_key is None and prompt_handler.key_is_caught is False:
                    time.sleep(0.1)

                key = prompt_handler.pressed_key
                prompt_handler.listen_to_keys = False
                prompt_handler.pressed_key = None
                prompt_handler.key_is_caught = False

                if key == "y" or key == "Y" or key == "\r":
                    gui_handler.debug_log("User approved shell execution")
                    PromptHandler.add_to_chat_history(response_message, "assistant")
                    shell_handler.execute(response_message)

                    # give power shell answer back to the ai (this could create a loop)
                    OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)
                else:
                    gui_handler.debug_log("User blocked shell execution")
                    gui_handler.print_text("SYSTEM INFO: \nShell execution blocked by user due to security issues.\n\n", TEXT_COLOR_SETTINGS)
                    PromptHandler.add_to_chat_history(response_message, "assistant")
                    PromptHandler.save_chat_history(prompt_handler.chat_history)

            else:  # if not in ask for execution mode - forward everything to the shell
                gui_handler.print_text(f"AI CODE: \n{response_message}\n\n", TEXT_COLOR_AI) 
                PromptHandler.add_to_chat_history(response_message, "assistant")
                shell_handler.execute(response_message)
                
                # give power shell answer back to the ai (this could create a loop)
                response_message = OpenAiHandler.generate_AI_response(prompt_handler.chat_history, openai_handler.OpenAiClient)

        elif answer_type == "empty": # if the ai response is none, then do nothing
            gui_handler.print_text(f"SYSTEM INFO: \nModel created empty reply message for the user.\n\n", TEXT_COLOR_SETTINGS)
        else: # if the ai response is neither, then print a warning
            gui_handler.print_text(f"SYSTEM INFO: \nDebug Warning: The forwarding decision is neither 'shell' nor 'user' but {answer_type}.\n\n", TEXT_COLOR_SETTINGS)

    
    # save current message stream to a txt file, give it the current date and time as name
    def save_chat_history(chat_history):
        current_time = time.strftime("%d.%m.%Y-%Hh%Mm%Ss")
        # ensure logs directory exists and build absolute target path
        base_path = os.getcwd()
        logs_dir = os.path.join(base_path, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, f"chat_history_{current_time}.txt")

        # save as txt file in utf8 for compatibility with other languages
        with open(log_path, "w", encoding="utf-8") as f:
            # transform list of dictionaries into string
            chat_history_string = ""
            for item in chat_history:
                role = item["role"]
                text = item["content"]
                chat_history_string += f"\n{role}: {text}\n"
            f.write(chat_history_string)
    
    # count the number of tokens in a string
    def num_tokens_from_string(string: str, encoding_name: str) -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

#-------------------------------------------------------
# Main
#-------------------------------------------------------

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