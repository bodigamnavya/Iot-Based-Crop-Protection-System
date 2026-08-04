import cv2
import winsound
from ultralytics import YOLO

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

print("AI Crop Protection System Started...")

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

                # Draw rectangle
                cv2.rectangle(frame,
                              (x1, y1),
                              (x2, y2),
                              (0,255,0),
                              2)

                # Display animal name
                cv2.putText(frame,
                            class_name,
                            (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0,255,0),
                            2)

    if animal_found:

        # Laptop Speaker Beep
        winsound.Beep(2000,500)

        cv2.putText(frame,
                    "ALERT : Animal Detected",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,255),
                    3)

    cv2.imshow("AI Crop Protection System", frame)

    # Press ESC to exit
    if cv2.waitKey(1) == 27:
        break

camera.release()

cv2.destroyAllWindows()