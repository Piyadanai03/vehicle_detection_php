# Vehicle Detection System

ระบบตรวจจับและนับยานพาหนะ โดยใช้ YOLOv8 สำหรับการเก็บตัวอักษร PHP backend และ MySQL database

## สถาปัตยกรรมของ Project

```
vehicle_detection_php/
├── backend/           # PHP API server
│   ├── controllers/   # VehicleController
│   ├── routes/        # API routes
│   ├── config/        # Database config
│   ├── Dockerfile     # Docker config
│   └── index.php      # Main entry point
├── yolo/              # YOLOv8 detection script
│   ├── main.py        # Main detection script
│   ├── tracker.py     # Object tracker
│   └── requirements.txt
├── db/                # Database initialization
│   └── database_init.sql
└── docker-compose.yml # Docker compose config
```

## ข้อกำหนดระบบ

- PHP 8.2+
- Python 3.8+
- MySQL 8.0+
- Docker & Docker Compose (optional)

## การติดตั้ง

### 1. Database Setup

ตั้งค่า MySQL database:

```sql
# Run the init script
source db/database_init.sql
```

หรือใช้ Docker Compose:

```bash
# เตรียม database environment
# Update docker-compose.yml ด้วย MySQL credentials ของคุณ
```

### 2. Backend (PHP API)

#### Option A: ใช้ Docker

```bash
# Build and run
docker-compose up --build

# API จะเข้าถึงได้ที่ http://localhost:8000
```

#### Option B: Local PHP

```bash
# ไปที่ backend directory
cd backend

# รัน PHP built-in server
php -S localhost:8000 index.php
```

**เปลี่ยน Port:**

แก้ไขใน `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "YOUR_PORT:8000"  # เปลี่ยน YOUR_PORT (เช่น 9000)
```

หรือ local (แก้ไข backend command):
```bash
php -S localhost:YOUR_PORT index.php  # เปลี่ยน YOUR_PORT
```

### 3. YOLO Detection (Python)

```bash
# ไปที่ yolo directory
cd yolo

# สร้าง virtual environment
py -m venv venv

# เปิดใช้งาน virtual environment
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt

# รัน detection script
py main.py
```

## Configuration

### Database Configuration

แก้ไข `backend/config/database.php`:

```php
$host = getenv('DB_HOST') ?: 'localhost';
$db   = getenv('DB_NAME') ?: 'cctv_traffic_db';
$user = getenv('DB_USER') ?: 'user';
$pass = getenv('DB_PASS') ?: 'password';
```

### Environment Variables (Docker)

แก้ไข `docker-compose.yml`:

```yaml
environment:
  - DB_HOST=your_host
  - DB_NAME=your_database
  - DB_USER=your_user
  - DB_PASS=your_password
```

### YOLO Configuration

แก้ไข `yolo/main.py`:

```python
# กำหนด Backend URL
BACKEND_URL = "http://localhost:8000/vehicle_count/"

# กำหนด Device Token
token = "dajsdkasjdsuad2348werwerewfjslfj8w424"

# กำหนด Camera ID
camera_id = 1

# กำหนด Video Path
video_path = '2025-02-18 11-02-09.mkv'
```

## API Endpoints

### 1. บันทึกข้อมูลการตรวจจับ

**POST** `/vehicle_count/`

Request body:
```json
{
  "vehicle_type": "car",
  "direction": "in",
  "count": 5,
  "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
  "camera_id": 1
}
```

Response (Success):
```json
{
  "status": "success",
  "edge_device_id": 1
}
```

Response (Error):
```json
{
  "error": "Invalid input"
}
```

**valid vehicle_type:** `car`, `motorcycle`, `bus`  
**valid direction:** `in`, `out`

---

### 2. ดึงข้อมูลสรุปยานพาหนะ

**GET** `/vehicle_count/all/(camera=ID|gate=ID)&start=YYYY-MM-DD&stop=YYYY-MM-DD`

#### ตัวอย่าง Query by Camera ID:

```
GET /vehicle_count/all/camera=1&start=2025-02-18&stop=2025-02-20
```

Response:
```json
{
  "data": [
    {
      "camera_id": 1,
      "vehicle_type": "car",
      "direction": "in",
      "count": 15
    },
    {
      "camera_id": 1,
      "vehicle_type": "car",
      "direction": "out",
      "count": 12
    }
  ]
}
```

#### ตัวอย่าง Query by Gate ID:

```
GET /vehicle_count/all/gate=1&start=2025-02-18&stop=2025-02-20
```

Response:
```json
{
  "data": [
    {
      "camera_id": 1,
      "vehicle_type": "car",
      "direction": "in",
      "count": 27
    },
    {
      "camera_id": 2,
      "vehicle_type": "motorcycle",
      "direction": "out",
      "count": 8
    }
  ]
}
```

## ตัวอย่างการทดสอบ API

### ใช้ cURL

#### 1. บันทึกข้อมูลยานพาหนะ

```bash
# ตัวอย่าง 1: นับรถยนต์เข้า 5 คัน
curl -X POST http://localhost:8000/vehicle_count/ \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type": "car",
    "direction": "in",
    "count": 5,
    "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
    "camera_id": 1
  }'

# ตัวอย่าง 2: นับรถจักรยานยนต์ออก 3 คัน
curl -X POST http://localhost:8000/vehicle_count/ \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type": "motorcycle",
    "direction": "out",
    "count": 3,
    "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
    "camera_id": 1
  }'

# ตัวอย่าง 3: นับรถบัสเข้า 2 คัน
curl -X POST http://localhost:8000/vehicle_count/ \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_type": "bus",
    "direction": "in",
    "count": 2,
    "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
    "camera_id": 1
  }'
```

#### 2. ดึงข้อมูลสรุป (By Camera)

```bash
# สรุปข้อมูลกล้อง 1 ระหว่าง 18-20 Feb
curl -X GET "http://localhost:8000/vehicle_count/all/camera=1&start=2025-02-18&stop=2025-02-20"

# สรุปข้อมูลกล้อง 2 ระหว่าง 10-28 Feb
curl -X GET "http://localhost:8000/vehicle_count/all/camera=2&start=2025-02-10&stop=2025-02-28"
```

#### 3. ดึงข้อมูลสรุป (By Gate)

```bash
# สรุปข้อมูล Gate 1 ระหว่าง 18-20 Feb
curl -X GET "http://localhost:8000/vehicle_count/all/gate=1&start=2025-02-18&stop=2025-02-20"

# สรุปข้อมูล Gate 2 ระหว่าง 10-28 Feb
curl -X GET "http://localhost:8000/vehicle_count/all/gate=2&start=2025-02-10&stop=2025-02-28"
```

### ใช้ Postman

Postman Collection format (copy ไปใน Postman):

#### 1. POST - บันทึกรถยนต์เข้า

```
Method: POST
URL: http://localhost:8000/vehicle_count/
Headers: Content-Type: application/json
Body (raw/JSON):
{
  "vehicle_type": "car",
  "direction": "in",
  "count": 5,
  "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
  "camera_id": 1
}
```

#### 2. POST - บันทึกรถจักรยานยนต์ออก

```
Method: POST
URL: http://localhost:8000/vehicle_count/
Headers: Content-Type: application/json
Body (raw/JSON):
{
  "vehicle_type": "motorcycle",
  "direction": "out",
  "count": 3,
  "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
  "camera_id": 1
}
```

#### 3. POST - บันทึกรถบัสเข้า

```
Method: POST
URL: http://localhost:8000/vehicle_count/
Headers: Content-Type: application/json
Body (raw/JSON):
{
  "vehicle_type": "bus",
  "direction": "in",
  "count": 2,
  "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
  "camera_id": 1
}
```

#### 4. GET - ดึงข้อมูลสรุปตามกล้อง

```
Method: GET
URL: http://localhost:8000/vehicle_count/all/camera=1&start=2025-02-18&stop=2025-02-20
Headers: Content-Type: application/json
```

#### 5. GET - ดึงข้อมูลสรุปตามประตู

```
Method: GET
URL: http://localhost:8000/vehicle_count/all/gate=1&start=2025-02-18&stop=2025-02-20
Headers: Content-Type: application/json
```

### ใช้ Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# POST - บันทึกข้อมูล
def test_post_vehicle_count():
    url = f"{BASE_URL}/vehicle_count/"
    payload = {
        "vehicle_type": "car",
        "direction": "in",
        "count": 5,
        "token": "dajsdkasjdsuad2348werwerewfjslfj8w424",
        "camera_id": 1
    }
    response = requests.post(url, json=payload)
    print(f"POST Response: {response.json()}")

# GET - ดึงข้อมูลตามกล้อง
def test_get_by_camera():
    url = f"{BASE_URL}/vehicle_count/all/camera=1&start=2025-02-18&stop=2025-02-20"
    response = requests.get(url)
    print(f"GET (Camera) Response: {response.json()}")

# GET - ดึงข้อมูลตามประตู
def test_get_by_gate():
    url = f"{BASE_URL}/vehicle_count/all/gate=1&start=2025-02-18&stop=2025-02-20"
    response = requests.get(url)
    print(f"GET (Gate) Response: {response.json()}")

if __name__ == "__main__":
    test_post_vehicle_count()
    test_get_by_camera()
    test_get_by_gate()
```

## Database Schema

### Tables

- **EdgeDevice**: ข้อมูลอุปกรณ์ขอบ (Edge devices)
- **VehicleType**: ประเภทยานพาหนะ (car, motorcycle, bus)
- **DirectionType**: ทิศทางการเคลื่อนที่ (in, out)
- **Gate**: ประตูวัน/สถานที่
- **Camera**: กล้อง CCTV
- **DetectionRecord**: บันทึกการตรวจจับ

### Initial Data

```sql
-- VehicleType
car, motorcycle, bus

-- DirectionType
in, out

-- Gate
Gate 1, Gate 2, Gate 3, Gate 4

-- EdgeDevice
CCTV-Edge-01 (token: dajsdkasjdsuad2348werwerewfjslfj8w424)

-- Camera
Camera-01 (Gate 1), Camera-02 (Gate 1), Camera-03 (Gate 2)
```

## Troubleshooting

### Database Connection Error

- ตรวจสอบ MySQL server ว่าทำงานอยู่
- ตรวจสอบ credentials ใน `database.php`
- ตรวจสอบ network access (โดยเฉพาะสำหรับ Docker)

### YOLO Script Error

- ตรวจสอบว่า virtual environment ถูกเปิดใช้งาน
- ตรวจสอบว่า requirements ติดตั้งครบ: `pip install -r requirements.txt`
- ตรวจสอบไฟล์ video path มีอยู่จริง
- ตรวจสอบการเชื่อมต่อ backend

### API Response Error

- ตรวจสอบ token ในการร้องขอ
- ตรวจสอบว่า vehicle_type และ direction ถูกต้อง
- ตรวจสอบว่า camera_id มีอยู่ในฐานข้อมูล
- ตรวจสอบ date format: `YYYY-MM-DD`

## Notes

- ไฟล์ `yolov8n.pt` และ `yolov8n-seg.pt` จำเป็นต้องมีอยู่ใน `yolo/` directory
- Backend ต้องทำงานก่อนที่จะเรียก API จาก YOLO script
- Database ต้องจัดตั้งและเตรียมข้อมูลเบื้องต้นก่อนการทำงาน

## License

MIT
