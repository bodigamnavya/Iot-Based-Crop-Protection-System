from playsound import playsound
import os

path = os.path.join(os.path.dirname(__file__), "alarm.wav")

print("Path:", path)

if os.path.exists(path):
    print("Alarm Found")
    playsound(path)
    print("Alarm Played")
else:
    print("alarm.wav not found")