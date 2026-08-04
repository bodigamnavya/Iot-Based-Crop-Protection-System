import cv2
import pyttsx3
from ultralytics import YOLO

# Voice Engine
engine = pyttsx3.init()

# Load YOLO model
model = YOLO("yolov8n.pt")

# Open Camera
camera = cv2.VideoCapture(0)

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

spoken = False

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

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

                cv2.putText(frame,
                            class_name,
                            (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0,255,0),
                            2)

    if animal_found and not spoken:
        engine.say("Warning! Animal detected. Please protect your crops.")
        engine.runAndWait()
        spoken = True

    if not animal_found:
        spoken = False

    cv2.imshow("AI Crop Protection System", frame)

    if cv2.waitKey(1) == 27:
        break

camera.release()
cv2.destroyAllWindows()