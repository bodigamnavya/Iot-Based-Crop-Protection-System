import random
from datetime import datetime
from flask_mysqldb import MySQL


def get_soil_moisture():

    moisture = random.randint(20, 80)

    if moisture < 40:
        pump_status = "ON"
    else:
        pump_status = "OFF"

    return moisture, pump_status

if __name__ == "__main__":

    moisture, pump = get_soil_moisture()

    print("Soil Moisture:", moisture)

    print("Pump Status:", pump)