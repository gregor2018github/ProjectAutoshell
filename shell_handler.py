"""Handles PowerShell commands and output."""

import os
import subprocess
import app_globals
from prompt_handler import PromptHandler

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
        os.chdir(app_globals.gui_handler_object.log_path)

        # make it utf-8 so that also korean or russian characters can be saved
        with open(filename, "a", encoding="utf-8") as f:
            f.write("commands:\n")
            f.write(commands)
            f.write("\n\noutput:\n")
            f.write(shell_output)
        os.chdir(app_globals.gui_handler_object.main_path)

    def execute(self, commands):
        self.send_shell_commands(commands)
        shell_output = self.catch_shell_output()
        self.save_to_file(shell_output, commands, "complete_command_history.txt")

        app_globals.gui_handler_object.print_text(f"POWER SHELL: \n{shell_output}\n\n", "red") 

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
            app_globals.gui_handler_object.print_text(f"SYSTEM INFO: \nPower Shell Answer exceeds 1000 tokens and was thus shortened for the prompt history.\n\n", "light_blue")

        
        PromptHandler.add_to_chat_history(shell_output, "system")

        # save the message stream
        PromptHandler.save_chat_history(app_globals.prompt_handler_object.chat_history)
