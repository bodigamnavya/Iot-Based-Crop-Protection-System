from ultralytics import YOLO
import cv2
from datetime import datetime
import os
import threading
from playsound import playsound

# -----------------------------
# Load YOLO Model
# -----------------------------
model = YOLO("yolov8n.pt")

# -----------------------------
# Camera
# -----------------------------
cap = cv2.VideoCapture(0)

# -----------------------------
# Create Folder
# -----------------------------
if not os.path.exists("captured_images"):
    os.makedirs("captured_images")

# -----------------------------
# Alarm Function
# -----------------------------
alarm_on = False

def play_alarm():
    global alarm_on
    playsound("alarm.wav")
    alarm_on = False

# -----------------------------
# Main Loop
# -----------------------------
while True:

    ret, frame = cap.read()

    if not ret:
        break

    results = model(frame)

    annotated_frame = results[0].plot()

    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cv2.putText(
        annotated_frame,
        current_time,
        (10,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,255,0),
        2
    )

    animal_found = False

    for box in results[0].boxes:

        cls = int(box.cls[0])

        name = model.names[cls]

        if name in ["person","dog","cat","cow","horse","sheep","bird"]:

            animal_found = True

            cv2.putText(
                annotated_frame,
                "ALERT : " + name.upper(),
                (10,70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                3
            )

            if not alarm_on:

                print("Detected :", name)

                alarm_on = True

                threading.Thread(
                    target=play_alarm,
                    daemon=True
                ).start()

                filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"

                cv2.imwrite(
                    "captured_images/" + filename,
                    frame
                )

                with open("Detection_Log.txt","a") as file:
                    file.write(f"{current_time} --> {name}\n")

            break

    if not animal_found:
        alarm_on = False

    cv2.imshow("AI Crop Protection System", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()