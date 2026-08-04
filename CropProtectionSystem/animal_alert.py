import cv2
import serial
import time
from ultralytics import YOLO

# Connect to Arduino
arduino = serial.Serial("COM3", 9600)
time.sleep(2)

# Load YOLO model
model = YOLO("yolov8n.pt")

# Open webcam
camera = cv2.VideoCapture(0)

# Animals to detect
animals = [
    "cat",
    "dog",
    "cow",
    "horse",
    "sheep",
    "elephant",
    "bear",
    "zebra",
    "giraffe"
]

while True:

    success, frame = camera.read()

    if not success:
        break

    results = model(frame)

    animal_found = False

    for result in results:

        for box in result.boxes:

            class_id = int(box.cls[0])

            class_name = model.names[class_id]

            if class_name in animals:

                animal_found = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame,
                            (x1, y1),
                            (x2, y2),
                            (0,255,0),
                            2)

                cv2.putText(frame,
                            class_name,
                            (x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0,255,0),
                            2)

    if animal_found:

        arduino.write(b'1')

        cv2.putText(frame,
                    "ALERT : Animal Detected",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,255),
                    3)

    else:

        arduino.write(b'0')

    cv2.imshow("AI Crop Protection",frame)

    if cv2.waitKey(1)==27:
        break

camera.release()

arduino.close()

cv2.destroyAllWindows()