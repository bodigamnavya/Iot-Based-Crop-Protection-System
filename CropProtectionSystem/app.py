import os
import sys

base_dir = os.path.abspath(os.path.dirname(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS
import cv2
from ultralytics import YOLO
import psycopg2
from alarm import play_alarm
from water_sensor import get_soil_moisture
from datetime import datetime
import time

app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, "templates"),
    static_folder=os.path.join(base_dir, "static")
)

# Enable CORS for all routes (supports Vercel and localhost)
CORS(app)


# ============================================================
# PostgreSQL Database Connection
# ============================================================

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url)
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        database=os.environ.get("PGDATABASE", "crop_protection"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "Navya09"),
        port=os.environ.get("PGPORT", "5432")
    )


# ============================================================
# Test PostgreSQL Connection
# ============================================================

try:
    conn = get_db_connection()
    conn.close()
    print("PostgreSQL connected successfully!")
except Exception as e:
    print("PostgreSQL connection note (will retry on requests):", e)


# ============================================================
# Load YOLO Model
# ============================================================

model_path = os.path.join(base_dir, "yolov8n.pt")
if not os.path.exists(model_path):
    model_path = "yolov8n.pt"

try:
    model = YOLO(model_path)
except Exception as e:
    print("YOLO model initialization note:", e)
    model = None


# ============================================================
# Open Camera
# ============================================================

camera_available = False
try:
    camera = cv2.VideoCapture(0)
    if camera and camera.isOpened():
        camera_available = True
    else:
        print("WARNING: Local camera not available (normal in cloud deployment).")
except Exception as e:
    print("Camera init note:", e)
    camera = None


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

    if camera is None or not camera.isOpened():
        import numpy as np
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            blank_frame,
            "Camera Feed Active (Local Mode Required)",
            (30, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        ret, buffer = cv2.imencode(".jpg", blank_frame)
        if ret:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
        return

    while True:

        success, frame = camera.read()

        if not success:
            print("Camera frame could not be read.")
            break

        # YOLO animal detection
        if model is not None:
            results = model(frame)
        else:
            results = []

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
# REST API Endpoints (for Vercel/Frontend Integration)
# ============================================================

@app.route("/api/status")
def api_status():
    soil, pump = get_soil_moisture()
    return jsonify({
        "status": "Active",
        "animal": current_animal,
        "confidence": current_confidence,
        "soil": soil,
        "pump": pump
    })


@app.route("/api/sensor")
def api_sensor():
    soil, pump = get_soil_moisture()
    return jsonify({
        "soil_moisture": soil,
        "pump_status": pump
    })


@app.route("/api/history")
def api_history():
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
        rows = cursor.fetchall()
        data = [
            {
                "animal": r[0],
                "confidence": float(r[1]) if r[1] is not None else 0.0,
                "time": str(r[2]),
                "status": r[3]
            }
            for r in rows
        ]
    except Exception as e:
        print("API error (history):", e)
        data = []
    finally:
        cursor.close()
        conn.close()
    return jsonify(data)


@app.route("/api/water_history")
def api_water_history():
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
        rows = cursor.fetchall()
        data = [
            {
                "soil_moisture": r[0],
                "pump_status": r[1],
                "time": str(r[2])
            }
            for r in rows
        ]
    except Exception as e:
        print("API error (water history):", e)
        data = []
    finally:
        cursor.close()
        conn.close()
    return jsonify(data)


# ============================================================
# Health Check Endpoints
# ============================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "camera_available": camera_available,
        "yolo_loaded": model is not None
    })


@app.route("/db-health")
def db_health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({
            "database": "connected",
            "status": "ok"
        })
    except Exception as e:
        return jsonify({
            "database": "disconnected",
            "status": "error",
            "message": str(e)
        }), 500


# ============================================================
# Run Flask Application
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )