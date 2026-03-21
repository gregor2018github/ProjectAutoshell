# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Autoshell is a voice-controlled AI assistant for Windows PowerShell. It captures voice (or keyboard) input, sends it to OpenAI's API, and routes the AI response either back to the user (via TTS) or to a PowerShell subprocess for execution. The GUI is built with Tkinter.

## Running the Application

```bash
source autoshell_envi/Scripts/activate
python Autoshell.py
```

Requires the `OPENAI_API_KEY` environment variable to be set. No requirements.txt exists; dependencies are managed directly in the `autoshell_envi/` virtual environment.

## Architecture

The entire application lives in `Autoshell.py` as five classes plus a main function:

- **GuiHandler** — Tkinter GUI with recording controls, input mode switching (mic/keyboard), voice selection, and settings toggles
- **SoundHandler** — Audio recording (PyAudio), speech-to-text (Whisper), and text-to-speech (OpenAI TTS-1)
- **ShellHandler** — Spawns and manages a PowerShell subprocess; sends commands, captures output, logs history
- **OpenAiHandler** — Thin wrapper around OpenAI chat completions API
- **PromptHandler** — Manages chat history and the core routing logic: after each AI response, a lightweight "forwarding" call decides whether the response goes to "user" (display + TTS), "shell" (execute in PowerShell), or "empty" (no action)

All five handlers are instantiated as globals in `main()` and cross-reference each other directly.

### Response Routing Flow

1. User speaks or types → SoundHandler transcribes (or keyboard text is used directly)
2. PromptHandler adds user message to chat history → OpenAiHandler calls GPT
3. A second GPT call (forwarding decision) classifies the response as "user", "shell", or "empty"
4. "shell" responses are sent to ShellHandler for execution; "user" responses are spoken via TTS

### Key Files

- `files/pre_prompt_shell.txt` — System prompt instructing GPT to act as a PowerShell assistant; defines the `talk_to_user()` convention
- `files/pre_prompt_forwarder.txt` — System prompt for the routing classifier
- `logs/` — Auto-generated chat history and command history logs

## Key Dependencies

openai, pyaudio, pygame (audio playback), tiktoken (token counting), tkinter (stdlib)

## Current State

The code references `gpt-5-mini` as the model but the OpenAI API integration may need updating for newer model calling conventions (see latest commit message). The application is single-threaded—UI freezes during API calls and audio playback (noted as a known issue in ToDo.md).
