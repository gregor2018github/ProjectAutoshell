"""Handles recording and playback of audio, including speech-to-text and text-to-speech functionalities."""

import os
import pyaudio
import wave
import threading
import app_globals

# recording user-sound to text and playing ai-text to sound
class SoundHandler:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.voice_agent = "onyx"

    def start_recording(self, name)->bool:
        """Start recording audio from the microphone and save it to a file. Returns True if successful, False otherwise."""
        self.is_recording = True
        self.filename = name + ".wav"
        self.chunk = 1024
        self.FORMAT = pyaudio.paInt16
        self.channels = 1
        self.sample_rate = 44100
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
            app_globals.gui_handler_object.print_text(error_message, "red")
            return False  # Failed to start recording

    def stop_recording(self):
        os.chdir(app_globals.gui_handler_object.files_path)
        self.is_recording = False
        print("Recording completed.")
        wf = wave.open(self.filename, "wb")
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b"".join(self.frames))
        wf.close()
        self.frames = []
        os.chdir(app_globals.gui_handler_object.main_path)


    def text_to_speech(text, client, voice_agent):
        # go to file subdirectory
        speech_file_path = app_globals.gui_handler_object.files_path + "/generated_audio.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice_agent,
            input=text
        )
        response.stream_to_file(speech_file_path)
        app_globals.gui_handler_object.play_sound("generated_audio.mp3")
        #os.system("generated_audio.mp3")
    
    def speech_to_text(audio_file_path, client):
        # change directory to subdirectory
        os.chdir(app_globals.gui_handler_object.files_path)
        audio_file= open(audio_file_path, "rb")
        transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
        )
        # change directory back to main directory
        os.chdir(app_globals.gui_handler_object.main_path)
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
            app_globals.gui_handler_object.print_text(f"USER: \n{transcript.text}\n\n", "white") 
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
