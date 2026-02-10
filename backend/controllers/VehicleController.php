<?php

class VehicleController {

    public static function store($db) {
        header('Content-Type: application/json');
        $data = json_decode(file_get_contents('php://input'), true);

        if (!isset($data['vehicle_type'], $data['direction'], $data['count'], $data['token'], $data['camera_id'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid input']);
            exit;
        }

        try {
            $vehicleTypeStmt = $db->prepare("SELECT id FROM VehicleType WHERE name = ?");
            $vehicleTypeStmt->execute([$data['vehicle_type']]);
            $vehicleType = $vehicleTypeStmt->fetch();
            if (!$vehicleType) throw new Exception("Invalid vehicle type: " . $data['vehicle_type']);

            $directionTypeStmt = $db->prepare("SELECT id FROM DirectionType WHERE name = ?");
            $directionTypeStmt->execute([$data['direction']]);
            $directionType = $directionTypeStmt->fetch();
            if (!$directionType) throw new Exception("Invalid direction: " . $data['direction']);

            $deviceStmt = $db->prepare("SELECT id FROM EdgeDevice WHERE token = ?");
            $deviceStmt->execute([$data['token']]);
            $device = $deviceStmt->fetch();
            if (!$device) throw new Exception("Invalid or missing device token");

            $cameraStmt = $db->prepare("SELECT id FROM Camera WHERE id = ?");
            $cameraStmt->execute([$data['camera_id']]);
            $camera = $cameraStmt->fetch();
            if (!$camera) throw new Exception("Invalid camera_id: " . $data['camera_id']);

            $stmt = $db->prepare("INSERT INTO DetectionRecord (edge_device_id, camera_id, vehicle_type_id, direction_type_id, count, time) VALUES (?, ?, ?, ?, ?, NOW())");
            $stmt->execute([
                $device['id'],
                $camera['id'],
                $vehicleType['id'],
                $directionType['id'],
                $data['count']
            ]);

            echo json_encode(['status' => 'success', 'edge_device_id' => $device['id']]);

        } catch (Exception $e) {
            error_log($e->getMessage());
            http_response_code(500);
            echo json_encode(['error' => 'Internal Server Error']);
        }
    }

    public static function summary($db) {
        header('Content-Type: application/json');
        $uri = $_SERVER['REQUEST_URI'];

        if (preg_match('#/vehicle_count/all/(camera|gate)=(\d+)&start=([\d\-]+)&stop=([\d\-]+)#', $uri, $matches)) {
            $type = $matches[1];
            $id = $matches[2];
            $start = $matches[3];
            $stop = $matches[4];

            try {
                $data = [];

                $vehicleTypes = $db->query("SELECT id, name FROM VehicleType")->fetchAll(PDO::FETCH_ASSOC);
                $directionTypes = $db->query("SELECT id, name FROM DirectionType")->fetchAll(PDO::FETCH_ASSOC);

                $vehicleTypeMap = [];
                foreach ($vehicleTypes as $vt) $vehicleTypeMap[$vt['id']] = $vt['name'];
                
                $directionTypeMap = [];
                foreach ($directionTypes as $dt) $directionTypeMap[$dt['id']] = $dt['name'];

                $vehicleTypeIds = array_column($vehicleTypes, 'id');
                $directionTypeIds = array_column($directionTypes, 'id');

                if ($type === 'gate') {
                    $stmt = $db->prepare("SELECT id FROM Camera WHERE gate_id = ?");
                    $stmt->execute([$id]);
                    $camera_ids = $stmt->fetchAll(PDO::FETCH_COLUMN);

                    if (empty($camera_ids)) {
                        echo json_encode(['data' => []]);
                        return;
                    }

                    $in = str_repeat('?,', count($camera_ids) - 1) . '?';
                    $sql = "SELECT camera_id, vehicle_type_id, direction_type_id, SUM(count) as count
                            FROM DetectionRecord
                            WHERE camera_id IN ($in) AND time BETWEEN ? AND ?
                            GROUP BY camera_id, vehicle_type_id, direction_type_id";
                    
                    $params = array_merge($camera_ids, [$start . " 00:00:00", $stop . " 23:59:59"]);
                    $stmt = $db->prepare($sql);
                    $stmt->execute($params);
                    $records = $stmt->fetchAll();

                    $grouped = [];
                    foreach ($camera_ids as $cid) {
                        $grouped[$cid] = [
                            'gate_id' => (int)$id,
                            'camera_id' => (int)$cid,
                            'start' => $start,
                            'stop' => $stop,
                            'details' => []
                        ];
                        foreach ($vehicleTypeIds as $vtid) {
                            foreach ($directionTypeIds as $dtid) {
                                $grouped[$cid]['details']["$vtid-$dtid"] = [
                                    'vehicle_type_id' => (int)$vtid,
                                    'vehicle_type_name' => $vehicleTypeMap[$vtid],
                                    'direction_type_id' => (int)$dtid,
                                    'direction_type_name' => $directionTypeMap[$dtid],
                                    'count' => 0
                                ];
                            }
                        }
                    }
                    
                    foreach ($records as $row) {
                        $cid = $row['camera_id'];
                        $vtid = $row['vehicle_type_id'];
                        $dtid = $row['direction_type_id'];
                        if(isset($grouped[$cid])) {
                            $grouped[$cid]['details']["$vtid-$dtid"]['count'] = (int)$row['count'];
                        }
                    }

                    foreach ($grouped as $cam) {
                        $cam['details'] = array_values($cam['details']);
                        $data[] = $cam;
                    }
                    echo json_encode(['data' => $data]);

                } else {
                    $stmt = $db->prepare("SELECT gate_id FROM Camera WHERE id = ?");
                    $stmt->execute([$id]);
                    $gate_id = $stmt->fetchColumn();

                    $sql = "SELECT vehicle_type_id, direction_type_id, SUM(count) as count
                            FROM DetectionRecord
                            WHERE camera_id = ? AND time BETWEEN ? AND ?
                            GROUP BY vehicle_type_id, direction_type_id";
                    
                    $params = [$id, $start . " 00:00:00", $stop . " 23:59:59"];
                    $stmt = $db->prepare($sql);
                    $stmt->execute($params);
                    $records = $stmt->fetchAll();

                    $details = [];
                    foreach ($vehicleTypeIds as $vtid) {
                        foreach ($directionTypeIds as $dtid) {
                            $details["$vtid-$dtid"] = [
                                'vehicle_type_id' => (int)$vtid,
                                'vehicle_type_name' => $vehicleTypeMap[$vtid],
                                'direction_type_id' => (int)$dtid,
                                'direction_type_name' => $directionTypeMap[$dtid],
                                'count' => 0
                            ];
                        }
                    }

                    foreach ($records as $row) {
                        $vtid = $row['vehicle_type_id'];
                        $dtid = $row['direction_type_id'];
                        $details["$vtid-$dtid"]['count'] = (int)$row['count'];
                    }

                    $data[] = [
                        'gate_id' => $gate_id !== false ? (int)$gate_id : null,
                        'camera_id' => (int)$id,
                        'start' => $start,
                        'stop' => $stop,
                        'details' => array_values($details)
                    ];
                    echo json_encode(['data' => $data]);
                }

            } catch (Exception $e) {
                error_log($e->getMessage());
                http_response_code(500);
                echo json_encode(['error' => 'Internal Server Error']);
            }

        } else {
            http_response_code(400);
            echo json_encode(['error' => 'Invalid parameters']);
            exit;
        }
    }
}