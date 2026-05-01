import time
import cv2
from utils.logger import logger
from config import TARGET_CLASSES, CLASS_LIST
from services.api_client import send_count_to_backend

class VehicleCounter:
    def __init__(self):
        self.counts = {c: {'out': [], 'in': []} for c in TARGET_CLASSES}
        self.vehicle_types = {} 
        self.vehicle_states = {}
        self.last_sent_counts = {c: {'out': 0, 'in': 0} for c in TARGET_CLASSES}
        self.last_send_time = time.time()

    def process_tracking(self, bbox_id, px_df, red_line_x, blue_line_x, frame):
        """วิเคราะห์ทิศทางและจับคู่ ID รถกับประเภท"""
        for bbox in bbox_id:
            x3, y3, x4, y4, obj_id = bbox
            cx, cy = (x3 + x4) // 2, (y3 + y4) // 2
            
            # จับคู่ Class กับ ID
            if px_df is not None:
                for _, row in px_df.iterrows():
                    box_cx, box_cy = (int(row[0]) + int(row[2])) // 2, (int(row[1]) + int(row[3])) // 2
                    if abs(cx - box_cx) < 10 and abs(cy - box_cy) < 10:
                        class_id = int(row[5])
                        if class_id < len(CLASS_LIST):
                            self.vehicle_types[obj_id] = CLASS_LIST[class_id]
                            break
            
            v_type = self.vehicle_types.get(obj_id)
            if not v_type or v_type not in TARGET_CLASSES:
                continue

            # วาดกรอบและ Label
            cv2.rectangle(frame, (x3, y3), (x4, y4), (255, 0, 0), 2)
            cv2.putText(frame, f'{v_type}', (x3, y3-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # --- Logic ข้ามเส้นแดง (Out) ---
            prev_red = self.vehicle_states.get((obj_id, 'red'))
            current_red = 'left' if cx < red_line_x else 'right'
            self.vehicle_states[(obj_id, 'red')] = current_red

            if prev_red == 'left' and current_red == 'right':
                if obj_id not in self.counts[v_type]['out']:
                    self.counts[v_type]['out'].append(obj_id)
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                    logger.info(f"ID {obj_id} ({v_type}) crossed RED - OUT")

            # --- Logic ข้ามเส้นน้ำเงิน (In) ---
            prev_blue = self.vehicle_states.get((obj_id, 'blue'))
            current_blue = 'left' if cx <= blue_line_x else 'right'
            self.vehicle_states[(obj_id, 'blue')] = current_blue

            if prev_blue == 'right' and current_blue == 'left':
                if obj_id not in self.counts[v_type]['in']:
                    self.counts[v_type]['in'].append(obj_id)
                    cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)
                    logger.info(f"ID {obj_id} ({v_type}) crossed BLUE - IN")

    def check_and_send_api(self):
        """ตรวจสอบและส่งข้อมูลทุก 10 วินาที"""
        current_time = time.time()
        if current_time - self.last_send_time >= 10:
            for v_type in TARGET_CLASSES:
                for direction in ['out', 'in']:
                    current_count = len(set(self.counts[v_type][direction]))
                    delta = current_count - self.last_sent_counts[v_type][direction]
                    if delta > 0:
                        send_count_to_backend(v_type, direction, delta)
                    self.last_sent_counts[v_type][direction] = current_count
            self.last_send_time = current_time

    def final_cleanup(self):
        """เคลียร์ข้อมูลคงค้างตอนปิดระบบ"""
        for v_type in TARGET_CLASSES:
            for direction in ['out', 'in']:
                current_count = len(set(self.counts[v_type][direction]))
                delta = current_count - self.last_sent_counts[v_type][direction]
                if delta > 0:
                    send_count_to_backend(v_type, direction, delta)