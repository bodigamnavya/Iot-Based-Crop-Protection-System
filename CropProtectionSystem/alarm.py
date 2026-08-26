import os
import winsound


def play_alarm():
    print("[ALARM] Animal detected! Playing alarm sound...")
    try:
        alarm_path = os.path.join(os.path.dirname(__file__), "alarm.wav")
        if os.path.exists(alarm_path):
            winsound.PlaySound(alarm_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(1000, 1000)
    except Exception as e:
        print("[ALARM] Audio playback error:", e)
