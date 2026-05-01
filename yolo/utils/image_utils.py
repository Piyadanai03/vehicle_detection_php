from config import ORANGE_WIDTH_RATIO, ORANGE_HEIGHT_RATIO

def get_custom_crop(frame):
    """ตัดภาพเอาเฉพาะมุมขวาล่างเพื่อประมวลผล"""
    height, width = frame.shape[:2]
    
    red_start_x = width // 2
    red_start_y = height // 2
    
    orange_width = int((width - red_start_x) * ORANGE_WIDTH_RATIO)
    orange_height = int((height - red_start_y) * ORANGE_HEIGHT_RATIO)
    
    orange_start_x = width - orange_width
    orange_start_y = height - orange_height
    
    return frame[orange_start_y:height, orange_start_x:width]