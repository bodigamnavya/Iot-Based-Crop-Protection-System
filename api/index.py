import os
import sys

# Ensure CropProtectionSystem is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
crop_sys_dir = os.path.join(root_dir, "CropProtectionSystem")

if crop_sys_dir not in sys.path:
    sys.path.insert(0, crop_sys_dir)

from app import app
