from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
from flask_mysqldb import MySQL
from alarm import play_alarm
from water_sensor import get_soil_moisture
from datetime import datetime

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))

mysql = MySQL(app)
# Load YOLO model
model = YOLO("yolov8n.pt")

# Open camera
camera = cv2.VideoCapture(0)
current_animal = "No Animal"
current_confidence = 0


# Home page
@app.route("/")
def index():

    # Get live soil moisture
    soil, pump = get_soil_moisture()

    # Save to MySQL
    cursor = mysql.connection.cursor()

    current_time = datetime.now()

    cursor.execute("""
    INSERT INTO Water_Management
    (Soil_Moisture, Pump_Status, Water_Time)
    VALUES (%s, %s, %s)
    """, (soil, pump, current_time))

    mysql.connection.commit()
    cursor.close()

    return render_template(
        "index.html",
        animal=current_animal,
        confidence=current_confidence,
        status="Active",
        soil=soil,
        pump=pump
    )
    
    


# Camera frame generation
def generate_frames():
    global current_animal, current_confidence

    while True:

        success, frame = camera.read()

        if not success:
            break

        # Animal detection
        results = model(frame)

        for result in results:

            for box in result.boxes:

                cls = int(box.cls[0])
                confidence = float(box.conf[0])
                if confidence < 0.60:
                    continue

                animal_name = model.names[cls]
                

                if animal_name in [
                    "elephant",
                    "dog",
                    "cow",
                    "cat",
                    "bird",
                    "horse",
                    "sheep"
                ]:
                    global current_animal, current_confidence

                    current_animal = animal_name
                    current_confidence = round(confidence * 100, 2)


                    print(
                        "Animal Detected:",
                        animal_name,
                        "Confidence:",
                        confidence
                    )
                    play_alarm()
                    
                    current_time = datetime.now()

                    cursor = mysql.connection.cursor()

                    cursor.execute("""
                    INSERT INTO Animal_Detection
                    (Animal_Name, Confidence, Detection_Time, Camera_ID, Alert_Status)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (animal_name, confidence, current_time, 1, "Active"))

                    mysql.connection.commit()
                    cursor.close()
                    
                    
                    # Display name on camera
                    cv2.putText(
                        frame,
                        animal_name,
                        (50,50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0,0,255),
                        2
                    )
                    


        # Convert frame
        ret, buffer = cv2.imencode(
            '.jpg',
            frame
        )

        frame = buffer.tobytes()


        # Send frame to browser
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame +
            b'\r\n'
        )



# Video streaming route
@app.route("/video")
def video():

    return Response(
        generate_frames(),
        mimetype=
        'multipart/x-mixed-replace; boundary=frame'
    )
@app.route("/history")

def history():

    cursor = mysql.connection.cursor()

    cursor.execute("""
    SELECT Animal_Name, Confidence, Detection_Time, Alert_Status
    FROM Animal_Detection
    ORDER BY Detection_ID DESC
    """)

    data = cursor.fetchall()

    cursor.close()

    return render_template("history.html", data=data)
@app.route("/water_history")
def water_history():

    cursor = mysql.connection.cursor()

    cursor.execute("""
    SELECT Soil_Moisture, Pump_Status, Water_Time
    FROM Water_Management
    ORDER BY Water_ID DESC
    """)

    data = cursor.fetchall()

    cursor.close()

    return render_template("water_history.html", data=data)


if __name__ == "__main__":

    app.run(
        debug=True
    )