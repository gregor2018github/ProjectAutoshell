import app_globals
from gui_handler import GuiHandler
from sound_handler import SoundHandler
from shell_handler import ShellHandler
from openai_handler import OpenAiHandler
from prompt_handler import PromptHandler

def main():
    
    # define the GUI
    app_globals.gui_handler_object = GuiHandler()

    # start connection to the powershell
    app_globals.shell_handler_object = ShellHandler()

    # start connection to the openai api
    app_globals.openai_handler_object = OpenAiHandler()

    # start the prompt handler
    app_globals.prompt_handler_object = PromptHandler()

    # start the sound handler
    app_globals.sound_handler_object = SoundHandler()

    # start the gui
    app_globals.gui_handler_object.start_gui()

if __name__ == '__main__':
    main()