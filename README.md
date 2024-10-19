Setup các thư viện với môi trường `nodejs >= 14.x` cho từng folder
```
npm install express@4.19.2 serialport@12.0.0 socket.io@4.7.5
```
Run code `node server.js`

Định dạng khi in ra Serila của arduino là giống như trên hình với mỗi data cách nhau 1 dấu `,` 

![Arduino](https://github.com/DoanCongQui/Web_Sensor/blob/main/img/Arduino.png)

- VD: Data trên là random vs 3 dữ liệu sẽ in ra `data1,data2,data3` đối với số dữ liệu khác hãy chĩnh sữa lại 
