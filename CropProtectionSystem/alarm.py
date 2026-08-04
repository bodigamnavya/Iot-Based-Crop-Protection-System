from playsound import playsound
import os

def play_alarm():
    sound_path = os.path.join(os.path.dirname(__file__), "alarm.wav")
    playsound(sound_path)