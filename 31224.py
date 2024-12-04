import serial
import time
import csv
import numpy as np
from collections import deque
import threading
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Cấu hình cảm biến
SERIAL_LEFT = "/dev/serial0"
SERIAL_RIGHT = "/dev/ttyUSB0"
BAUD_RATE = 115200

# Ngưỡng TTC và khoảng cách
TTC_THRESHOLD_HIGH = 5.0  # Giây
TTC_THRESHOLD_LOW = 3.0   # Giây
DISTANCE_THRESHOLD = 1.0  # Chênh lệch 1m giữa 2 cảm biến

# Lịch sử đo khoảng cách
HISTORY_LIMIT = 50
distance_left_history = deque(maxlen=HISTORY_LIMIT)
distance_right_history = deque(maxlen=HISTORY_LIMIT)

# Tên tệp CSV
CSV_FILE = "sensor_data.csv"

# Hàm đọc dữ liệu từ cảm biến TF-Luna
def read_tfluna_data(ser):
    while ser.in_waiting < 9:
        time.sleep(0.01)  # Chờ dữ liệu
    bytes_serial = ser.read(9)
    ser.reset_input_buffer()

    if bytes_serial[0] == 0x59 and bytes_serial[1] == 0x59:
        distance = bytes_serial[2] + bytes_serial[3] * 256
        strength = bytes_serial[4] + bytes_serial[5] * 256
        temperature = (bytes_serial[6] + bytes_serial[7] * 256) / 8.0 - 256.0
        return distance / 100.0, strength, temperature
    return None, None, None

# Hàm tính TTC
def calculate_ttc(distance, velocity):
    if velocity < 0:  # Vận tốc âm nghĩa là tiến gần
        return distance / abs(velocity)
    return float('inf')  # Không có nguy cơ va chạm

# Hàm xử lý dữ liệu
def process_data():
    while True:
        if len(distance_left_history) > 1 and len(distance_right_history) > 1:
            # Lấy dữ liệu mới nhất
            distance_left = distance_left_history[-1]
            distance_right = distance_right_history[-1]

            delta_time = 0.1  # Khoảng thời gian đo (100ms)

            # Tính vận tốc
            velocity_left = (distance_left_history[-1] - distance_left_history[-2]) / delta_time
            velocity_right = (distance_right_history[-1] - distance_right_history[-2]) / delta_time

            # Tính TTC
            ttc_left = calculate_ttc(distance_left, velocity_left)
            ttc_right = calculate_ttc(distance_right, velocity_right)

            # Xác định cảnh báo
            if ttc_left < TTC_THRESHOLD_LOW or ttc_right < TTC_THRESHOLD_LOW:
                collision_warning = "Nguy cơ cao: Va chạm sắp xảy ra!"
            elif ttc_left < TTC_THRESHOLD_HIGH or ttc_right < TTC_THRESHOLD_HIGH:
                collision_warning = "Nguy cơ trung bình: Cần chú ý!"
            else:
                collision_warning = "An toàn: Không có nguy cơ va chạm ngay lập tức."

            # Xác định hướng cảnh báo
            if abs(distance_left - distance_right) <= DISTANCE_THRESHOLD:
                warning_direction = "middle"
            elif distance_left < distance_right - DISTANCE_THRESHOLD:
                warning_direction = "left"
            else:
                warning_direction = "right"

            # Lưu vào tệp CSV
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([current_time, distance_left, 0, 0, 
                                 distance_right, 0, 0, 
                                 velocity_left, velocity_right, warning_direction, 
                                 ttc_left, ttc_right, collision_warning])

            # Hiển thị kết quả
            print(f"[{current_time}]")
            print(f"  Trái  : {distance_left:.2f}m, TTC: {ttc_left:.2f}s")
            print(f"  Phải  : {distance_right:.2f}m, TTC: {ttc_right:.2f}s")
            print(f"  Cảnh báo: {collision_warning}")
            print(f"  Hướng cảnh báo: {warning_direction}")
            print(f"  Thời gian va chạm (nếu tiến gần):")
            print(f"    - Trái: {ttc_left:.2f}s")
            print(f"    - Phải: {ttc_right:.2f}s")
        time.sleep(0.1)  # 100ms chờ xử lý tiếp theo

# Hàm đọc dữ liệu từ cảm biến
def read_sensor_data(ser, history):
    while True:
        distance, strength, temperature = read_tfluna_data(ser)
        if distance is not None:
            history.append(distance)
        time.sleep(0.1)

# Kiểm tra và xử lý dữ liệu
def preprocess_data(X):
    # Kiểm tra giá trị vô cùng và NaN
    X = np.array(X)  # Đảm bảo X là numpy array
    if np.any(np.isinf(X)) or np.any(np.isnan(X)):
        print("Dữ liệu chứa giá trị vô cùng (infinity) hoặc NaN!")
        # Loại bỏ các hàng chứa giá trị vô cùng hoặc NaN
        X = X[~np.isnan(X).any(axis=1)]
        X = X[~np.isinf(X).any(axis=1)]
    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X

# Huấn luyện mô hình Random Forest
def train_random_forest():
    # Lấy dữ liệu đã lưu từ CSV
    data = []
    with open(CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)
    
    # Chuyển dữ liệu thành numpy array và tách các đặc trưng và nhãn
    data = np.array(data)
    X = data[:, 1:9]  # Các đặc trưng từ cột 1 đến cột 8
    y = data[:, 10]   # Nhãn (cột cảnh báo)

    # Tiền xử lý dữ liệu
    X = preprocess_data(X)

    # Chia dữ liệu thành bộ huấn luyện và bộ kiểm tra
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Huấn luyện mô hình Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Kiểm tra mô hình
    accuracy = model.score(X_test, y_test)
    print(f"Độ chính xác của mô hình: {accuracy * 100:.2f}%")
    return model

# Khởi tạo cổng nối tiếp
ser_left = serial.Serial(SERIAL_LEFT, BAUD_RATE, timeout=0)
ser_right = serial.Serial(SERIAL_RIGHT, BAUD_RATE, timeout=0)

# Khởi tạo luồng
thread_left = threading.Thread(target=read_sensor_data, args=(ser_left, distance_left_history))
thread_right = threading.Thread(target=read_sensor_data, args=(ser_right, distance_right_history))
thread_process = threading.Thread(target=process_data)

# Khởi động các luồng
thread_left.start()
thread_right.start()
thread_process.start()

# Chờ các luồng kết thúc
thread_left.join()
thread_right.join()
thread_process.join()

# Huấn luyện mô hình Random Forest
model = train_random_forest()
