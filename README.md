**Setup các thư viện với môi trường `nodejs >= 14.x` cho từng folder**
```
npm install express@4.19.2 serialport@12.0.0 socket.io@4.7.5
```
**Run code `node server.js`**

**Lưu ý:**
- Phần `portpath` đã comment đối với Linux thì giữ nguyên không cần chỉnh sữa còn đối với Windows thì mở comment `Port COM4` và đóng comment port `/dev/ttyUSB0` lại
- Mỗi máy tính sẽ có 1 cổng COM khác nhau
![Port](https://github.com/DoanCongQui/Web_Sensor/blob/main/img/Port.png)

**File Arduino**

Định dạng khi in ra Serila của arduino là giống như trên hình với mỗi data cách nhau 1 dấu `,` 

![Arduino](https://github.com/DoanCongQui/Web_Sensor/blob/main/img/Arduino.png)

- VD: Data trên là random vs 3 dữ liệu sẽ in ra `data1,data2,data3`.
