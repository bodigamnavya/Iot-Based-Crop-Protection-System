import random


def get_soil_moisture():

    # Generate soil moisture value
    moisture = random.randint(20, 80)

    # Decide pump status
    if moisture < 40:
        pump_status = "ON"
    else:
        pump_status = "OFF"

    return moisture, pump_status


# Test the sensor
if __name__ == "__main__":

    moisture, pump = get_soil_moisture()

    print("Soil Moisture:", moisture)
    print("Pump Status:", pump)