from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
import psycopg2
from alarm import play_alarm
from water_sensor import get_soil_moisture
from datetime import datetime
import time


app = Flask(__name__)


# ============================================================
# PostgreSQL Database Connection
# ============================================================

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="crop_protection",
        user="postgres",
        password="Navya09",
        port="5432"
    )


# ============================================================
# Test PostgreSQL Connection
# ============================================================

try:
    conn = get_db_connection()
    conn.close()
    print("PostgreSQL connected successfully!")
except Exception as e:
    print("PostgreSQL connection failed:")
    print(e)


# ============================================================
# Load YOLO Model
# ============================================================

model = YOLO("yolov8n.pt")


# ============================================================
# Open Camera
# ============================================================

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("WARNING: Camera could not be opened.")


# ============================================================
# Current Detection Values
# ============================================================

current_animal = "No Animal"
current_confidence = 0


# ============================================================
# Detection Cooldown (seconds)
# ============================================================

DETECTION_COOLDOWN = 10
last_detection_time = 0


# ============================================================
# Home Page
# ============================================================

@app.route("/")
def index():

    # Get live soil moisture
    soil, pump = get_soil_moisture()

    # Connect to PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        current_time = datetime.now()

        # Save water management data
        cursor.execute(
            """
            INSERT INTO Water_Management
            (Soil_Moisture, Pump_Status, Water_Time)
            VALUES (%s, %s, %s)
            """,
            (soil, pump, current_time)
        )

        conn.commit()

    except Exception as e:
        print("Database error (water insert):", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "index.html",
        animal=current_animal,
        confidence=current_confidence,
        status="Active",
        soil=soil,
        pump=pump
    )


# ============================================================
# Camera Frame Generation + Animal Detection
# ============================================================

def generate_frames():

    global current_animal
    global current_confidence
    global last_detection_time

    while True:

        success, frame = camera.read()

        if not success:
            print("Camera frame could not be read.")
            break

        # YOLO animal detection
        results = model(frame)

        for result in results:

            for box in result.boxes:

                # Class ID
                cls = int(box.cls[0])

                # Confidence
                confidence = float(box.conf[0])

                # Ignore low-confidence detections
                if confidence < 0.60:
                    continue

                # Get detected object name
                animal_name = model.names[cls]

                # Allowed animals
                if animal_name in [
                    "elephant",
                    "dog",
                    "cow",
                    "cat",
                    "bird",
                    "horse",
                    "sheep"
                ]:

                    current_animal = animal_name

                    current_confidence = round(
                        confidence * 100,
                        2
                    )

                    # Display animal name on frame
                    cv2.putText(
                        frame,
                        animal_name,
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2
                    )

                    # Display confidence on frame
                    cv2.putText(
                        frame,
                        f"Confidence: {current_confidence}%",
                        (50, 90),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

                    # Cooldown check: only alarm + DB insert
                    # once per DETECTION_COOLDOWN seconds
                    now = time.time()

                    if now - last_detection_time >= DETECTION_COOLDOWN:

                        last_detection_time = now

                        print(
                            "Animal Detected:",
                            animal_name,
                            "| Confidence:",
                            current_confidence,
                            "%"
                        )

                        # Play alarm
                        play_alarm()

                        # Current date and time
                        current_time = datetime.now()

                        # Connect to PostgreSQL
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        try:
                            # Save animal detection
                            cursor.execute(
                                """
                                INSERT INTO Animal_Detection
                                (
                                    Animal_Name,
                                    Confidence,
                                    Detection_Time,
                                    Camera_ID,
                                    Alert_Status
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    animal_name,
                                    confidence,
                                    current_time,
                                    1,
                                    "Active"
                                )
                            )

                            conn.commit()

                        except Exception as e:
                            print("Database error (animal insert):", e)
                            conn.rollback()

                        finally:
                            cursor.close()
                            conn.close()


        # Convert frame to JPEG
        ret, buffer = cv2.imencode(
            ".jpg",
            frame
        )

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Send frame to browser
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


# ============================================================
# Video Streaming Route
# ============================================================

@app.route("/video")
def video():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ============================================================
# Animal Detection History
# ============================================================

@app.route("/history")
def history():

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                Animal_Name,
                Confidence,
                Detection_Time,
                Alert_Status
            FROM Animal_Detection
            ORDER BY Detection_ID DESC
            """
        )

        data = cursor.fetchall()

    except Exception as e:
        print("Database error (history):", e)
        data = []

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "history.html",
        data=data
    )


# ============================================================
# Water Management History
# ============================================================

@app.route("/water_history")
def water_history():

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                Soil_Moisture,
                Pump_Status,
                Water_Time
            FROM Water_Management
            ORDER BY Water_ID DESC
            """
        )

        data = cursor.fetchall()

    except Exception as e:
        print("Database error (water history):", e)
        data = []

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "water_history.html",
        data=data
    )


# ============================================================
# Run Flask Application
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )