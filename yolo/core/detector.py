import torch
import platform
import os
import pandas as pd
from ultralytics import YOLO
from utils.logger import logger
from config import MODEL_PATH, CLASS_LIST, TARGET_CLASSES

class VehicleDetector:
    def __init__(self):
        self.gpu_info = self._detect_gpu()
        self.model = self._load_model()
        self._configure_gpu()

    def _detect_gpu(self):
        info = {'device': 'cpu', 'name': 'CPU', 'backend': None}
        try:
            if torch.cuda.is_available():
                info.update({'device': 'cuda', 'name': torch.cuda.get_device_name(0), 'backend': 'cuda'})
                logger.info(f"NVIDIA GPU detected: {info['name']}")
            elif platform.system() == 'Windows':
                import win32com.client
                wmi = win32com.client.GetObject("winmgmts:")
                for gpu in wmi.InstancesOf("Win32_VideoController"):
                    if "AMD" in gpu.Name or "Radeon" in gpu.Name:
                        info.update({'device': 'cpu', 'name': gpu.Name, 'backend': 'rocm'})
                        logger.info(f"AMD GPU detected: {info['name']}")
                        return info
            if torch.backends.mps.is_available():
                info.update({'device': 'mps', 'name': 'Intel Graphics', 'backend': 'mps'})
                logger.info(f"Intel GPU detected: {info['name']}")
        except Exception as e:
            logger.error(f"Error detecting GPU: {e}")
        return info

    def _load_model(self):
        if not os.path.exists(MODEL_PATH):
            logger.info("Downloading YOLO model...")
            from ultralytics import download_from_hub
            download_from_hub(MODEL_PATH)
        return YOLO(MODEL_PATH)

    def _configure_gpu(self):
        backend = self.gpu_info['backend']
        if backend == 'cuda':
            self.model.to('cuda')
            torch.backends.cudnn.benchmark = True
        elif backend == 'rocm':
            os.environ['HSA_OVERRIDE_GFX_VERSION'] = '10.3.0'
            os.environ['HIP_VISIBLE_DEVICES'] = '0'
        elif backend == 'mps':
            self.model.to('mps')
            self.model.model.half()
        else:
            self.model.to('cpu')
            torch.set_num_threads(4)

    def predict(self, frame):
        """ประมวลผลเฟรมและคืนค่ากรอบวัตถุ (เฉพาะที่สนใจ) พร้อม Pandas DataFrame"""
        if self.gpu_info['backend'] == 'cuda':
            with torch.amp.autocast("cuda"):
                results = self.model.predict(frame, workers=4, verbose=False)
        else:
            results = self.model.predict(frame, workers=2, verbose=False)
            
        result = results[0]
        if len(result.boxes) == 0:
            return [], None
            
        a = result.boxes.data
        px = pd.DataFrame(a.cpu().numpy() if self.gpu_info['backend'] == 'cuda' else a.numpy()).astype("float")
        
        rect_list = []
        for index, row in px.iterrows():
            class_id = int(row[5])
            if class_id < len(CLASS_LIST) and CLASS_LIST[class_id] in TARGET_CLASSES:
                rect_list.append([int(row[0]), int(row[1]), int(row[2]), int(row[3])])
                
        return rect_list, px