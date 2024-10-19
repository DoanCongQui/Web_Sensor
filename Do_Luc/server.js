const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const { SerialPort } = require('serialport');
const Readline = require('@serialport/parser-readline').ReadlineParser;

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// const portPath = 'COM4';  // Windows
const portPath = '/dev/ttyUSB0';  // Linux/MacOS

let port;
let isArduinoPaused = false;

try {
    port = new SerialPort({ path: portPath, baudRate: 9600 });

    const parser = port.pipe(new Readline({ delimiter: '\r\n' }));

    parser.on('data', (data) => {
        if (!isArduinoPaused) {
            try {
                const [sensor1, sensor2, sensor3] = data.split(',').map(Number); // Chuyển đổi thành số 
                const sensorData = {
                    sensor1: parseFloat(sensor1),
                    sensor2: parseFloat(sensor2),
                    sensor3: parseFloat(sensor3)
                };
                console.log('Dữ liệu từ Arduino:', sensorData);
                io.emit('arduinoData', JSON.stringify(sensorData)); 
            } catch (err) {
                console.error('Lỗi phân tích dữ liệu Arduino:', err.message);
            }
        }
    });

    port.on('error', (err) => {
        console.error('Lỗi SerialPort:', err.message);
    });

} catch (err) {
    console.error('Lỗi khởi tạo SerialPort:', err.message);
}

app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
    console.log('Client đã kết nối');

    socket.on('stopArduino', () => {
        isArduinoPaused = true;
        port.write('STOP\n'); 
        console.log('Stop');
    });

    socket.on('startArduino', () => {
        isArduinoPaused = false;
        port.write('START\n');
        console.log('Start');
    });

    socket.on('disconnect', () => {
        console.log('Client đã ngắt kết nối');
    });
});

server.listen(3000, '0.0.0.0', () => {
    console.log('Listening on http://0.0.0.0:3000');
});
