import cv2
import sys
from config import VIDEO_PATH, TARGET_CLASSES
from core.detector import VehicleDetector
from core.tracker import Tracker
from core.counter import VehicleCounter
from utils.logger import logger
from utils.image_utils import get_custom_crop

def main():
    logger.info("Initializing System...")
    cv2.setUseOptimized(True)
    cv2.setNumThreads(4)

    # โหลด Modules
    detector = VehicleDetector()
    tracker = Tracker()
    counter = VehicleCounter()

    # ตั้งค่าวิดีโอ
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        logger.error(f"Failed to open video: {VIDEO_PATH}")
        sys.exit(1)

    cv2.namedWindow("Vehicle Counter", cv2.WINDOW_NORMAL)
    frame_count = 0
    start_time = cv2.getTickCount()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("End of video stream.")
                break

            # ตัดเฉพาะจุดที่สนใจและย่อขนาด
            quadrant = get_custom_crop(frame)
            resize_dim = (600, 450) if detector.gpu_info['backend'] in ['cuda', 'rocm'] else (400, 300)
            processed_frame = cv2.resize(quadrant, resize_dim, interpolation=cv2.INTER_AREA)
            
            frame_height, frame_width = processed_frame.shape[:2]
            red_line_x = int(frame_width * 0.85)
            blue_line_x = int(frame_width * 0.30)

            # ตรวจจับวัตถุ
            rect_list, px_df = detector.predict(processed_frame)
            
            # อัปเดตตำแหน่ง Tracker
            if rect_list:
                bbox_id = tracker.update(rect_list)
                # นับจำนวนและขีดเส้น
                counter.process_tracking(bbox_id, px_df, red_line_x, blue_line_x, processed_frame)

            # วาดเส้นบนจอ
            cv2.line(processed_frame, (red_line_x, int(frame_height*0.11)), (red_line_x, int(frame_height*0.54)), (0, 0, 255), 2)
            cv2.line(processed_frame, (blue_line_x, int(frame_height*0.40)), (blue_line_x, int(frame_height)), (255, 0, 0), 2)

            # แสดงผลยอดบนมุมซ้ายบน
            y_offset = 40
            cv2.putText(processed_frame, f"GPU: {detector.gpu_info['name']}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            for v_type in TARGET_CLASSES:
                out_cnt = len(set(counter.counts[v_type]["out"]))
                in_cnt = len(set(counter.counts[v_type]["in"]))
                cv2.putText(processed_frame, f'{v_type.capitalize()} Out: {out_cnt}', (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                cv2.putText(processed_frame, f'{v_type.capitalize()} In: {in_cnt}', (10, y_offset+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 40

            # ส่ง API (ถ้าถึงเวลา)
            counter.check_and_send_api()

            # แสดงผล FPS ทุก 30 เฟรม
            frame_count += 1
            if frame_count % 30 == 0:
                fps = frame_count / ((cv2.getTickCount() - start_time) / cv2.getTickFrequency())
                logger.info(f"FPS: {fps:.2f}")

            cv2.imshow("Vehicle Counter", processed_frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Cleaning up...")
        counter.final_cleanup()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()