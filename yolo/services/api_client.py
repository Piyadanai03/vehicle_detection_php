import requests
import json
from config import BACKEND_URL, TOKEN, CAMERA_ID
from utils.logger import logger

def send_count_to_backend(vehicle_type, direction, count):
    """ส่งข้อมูลการนับยานพาหนะไปยัง backend"""
    if count <= 0:
        return 
        
    try:
        payload = {
            "vehicle_type": vehicle_type,
            "direction": direction,
            "count": count,
            "token": TOKEN,      
            "camera_id": CAMERA_ID 
        }
        logger.info(f"Sending data to backend: {json.dumps(payload)}")
        
        response = requests.post(BACKEND_URL, json=payload, timeout=2)
        if response.status_code == 200:
            logger.info(f"Successfully sent data: {vehicle_type} {direction} count: {count}")
        else:
            logger.error(f"Failed to send data: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error - Unable to connect to {BACKEND_URL}")
    except Exception as e:
        logger.error(f"Error sending data to backend: {e}")