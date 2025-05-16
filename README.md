DESCRIPTION:

This Python program creates an AI assistant that can interact with your the windows PowerShell. It's called "Autoshell". 
The assistant is capable of understanding your voice, executing commands in the PowerShell, and answering via speech synthesis. 
This approach provides a nearly hands-free way to control your PC. The user steers the conversation via a GUI.

The program allows for a wide range of functionalities, like:
    - opening applications
    - get specifications about your PC (e.g. battery level, hardware components, network connections etc.)
    - create files and folders, navigate through your file system
    - shutdown, restart, log off, lock the PC
    - write and run little scripts
    - just chat with it in multiple languages

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

The preprompts are currently stored outside of the program for easy tinkering.

20.01.2024
