import os


def play_alarm():
    print("[ALARM] Animal detected! Triggering alert...")
    try:
        import winsound
        alarm_path = os.path.join(os.path.dirname(__file__), "alarm.wav")
        if os.path.exists(alarm_path):
            winsound.PlaySound(alarm_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.Beep(1000, 1000)
    except ImportError:
        # Non-Windows / cloud server environment
        print("[ALARM] Audio playback skipped in cloud server environment.")
    except Exception as e:
        print("[ALARM] Audio alert note:", e)

