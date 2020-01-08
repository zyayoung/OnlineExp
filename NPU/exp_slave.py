############################
# Configurations
############################

SSID        = "TP-LINK_AB74"
PASSWORD    = "young12345"
MASTER_IP   = "192.168.1.13"
DEVICE_NAME = "001"

import lcd
FONT_COLOT  = lcd.WHITE


############################
# Import
############################

from fpioa_manager import *
import machine

import sensor
import image
import lcd
import KPU as kpu

import os
import socket
import network
import gc
import uerrno
import sys

def clip(x, a, b):
    if x<a: x=a
    if x>b: x=b
    return x


############################
# Init lcd
############################

lcd.init()


############################
# Network
############################
lcd.draw_string(0, 18*0, "Mouse Tracker", FONT_COLOT, lcd.BLACK)
lcd.draw_string(0, 18*1, "Name: "+DEVICE_NAME, FONT_COLOT, lcd.BLACK)

try:
    fm.register(board_info.WIFI_RX,fm.fpioa.UART2_TX)
    fm.register(board_info.WIFI_TX,fm.fpioa.UART2_RX)
    uart = machine.UART(machine.UART.UART2,115200,timeout=2000, read_buf_len=4096)
    lcd.draw_string(0, 18*2, "Init WiFi ...", FONT_COLOT, lcd.BLACK)
    nic=network.ESP8285(uart)
    lcd.draw_string(0, 18*2, "Connecting to WiFi: "+SSID, FONT_COLOT, lcd.BLACK)
    nic.connect(SSID, PASSWORD)
except KeyError as e:
    lcd.draw_string(0, 18*3, str(e), FONT_COLOT, lcd.BLACK)
    sys.exit()
except OSError as e:
    lcd.draw_string(0, 18*3, str(e), FONT_COLOT, lcd.BLACK)
    sys.exit()
else:
    lcd.draw_string(0, 18*3, "WiFi Connected", FONT_COLOT, lcd.BLACK)



############################
# Socket
############################

lcd.draw_string(0, 18*4, "Connecting to Master: "+MASTER_IP, FONT_COLOT, lcd.BLACK)
try:
    addr = (MASTER_IP, 3456)
    sock = socket.socket()
    sock.connect(addr)
    sock.settimeout(5)

    sock.send(bytes(DEVICE_NAME, "ascii"))
except KeyError as e:
    lcd.draw_string(0, 18*5, "Failed: "+str(e), FONT_COLOT, lcd.BLACK)
    sys.exit()
except OSError as e:
    lcd.draw_string(0, 18*5, "Failed: "+str(e), FONT_COLOT, lcd.BLACK)
    sys.exit()
else:
    lcd.draw_string(0, 18*5, "Connected to Master", FONT_COLOT, lcd.BLACK)


############################
# Init camera
############################

lcd.draw_string(0, 18*6, "Initializing Camera...", FONT_COLOT, lcd.BLACK)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)

sensor.run(1)


############################
# Init yolo
############################
lcd.draw_string(0, 18*7, "Loading model...", FONT_COLOT, lcd.BLACK)
task = kpu.load("/sd/yolo.kmodel")
anchor = (0.750, 0.875, 2.875, 2.500, 2.625, 4.625, 5.625, 2.125, 4.625, 3.625)
a = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

lcd.draw_string(0, 18*8, "Done!", FONT_COLOT, lcd.BLACK)

############################
# Main loop
############################

frame_idx = 0
while(True):
    frame_idx += 1
    img = sensor.snapshot()
    if frame_idx % 300 == 30:
        # send image
        lcd.draw_string(0, 18*0, "Sending Image ...", FONT_COLOT, lcd.BLACK)
        img = img.compress()
        size = img.size()
        sent = 0
        while sent < size:
            sent += sock.send(bytearray(img[sent:]))
        continue
    code = kpu.run_yolo2(task, img)
    if code:
        info = b"Detections: "
        for i in code:
            print(i)
            x, y, w, h = i.rect()
            x += w//2
            y += h//2
            info += i.index().to_bytes(2, "little")
            info += x.to_bytes(2, "little")
            info += y.to_bytes(2, "little")
            info += w.to_bytes(2, "little")
            info += h.to_bytes(2, "little")
            info += int(i.value()*255).to_bytes(2, "little")
            a = img.draw_rectangle(i.rect())
        sock.send(info)
    a = lcd.display(img)
a = kpu.deinit(task)

sock.close()
