import sys
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
crop_dir = os.path.join(base_dir, "CropProtectionSystem")
if crop_dir not in sys.path:
    sys.path.insert(0, crop_dir)

from CropProtectionSystem.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
