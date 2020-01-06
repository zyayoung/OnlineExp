############################
# Configurations
############################

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
import video

def clip(x, a, b):
    if x<a: x=a
    if x>b: x=b
    return x


############################
# Init lcd
############################

lcd.init()
lcd.draw_string(0, 18*0, "Mouse Tracker Local", FONT_COLOT, lcd.BLACK)


############################
# Praparing Path
############################

try:
    os.mkdir("/sd/log")
except:
    pass
path_id = 0
while True:
    if str(path_id)+".avi" not in os.listdir("/sd/log"):
        break
    path_id += 1
filepath = "/sd/log/"+str(path_id)+".avi"
lcd.draw_string(0, 18*1, "Path: "+filepath, FONT_COLOT, lcd.BLACK)
#v = video.open(filepath, record=1, interval=100000, quality=50)

############################
# Init camera
############################

lcd.draw_string(0, 18*2, "Initializing Camera...", FONT_COLOT, lcd.BLACK)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(False)

sensor.run(1)


############################
# Init yolo
############################
lcd.draw_string(0, 18*3, "Loading model...", FONT_COLOT, lcd.BLACK)
task = kpu.load("/sd/yolo.kmodel")
anchor = (0.750, 0.875, 2.875, 2.500, 2.625, 4.625, 5.625, 2.125, 4.625, 3.625)
a = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

lcd.draw_string(0, 18*4, "Done!", FONT_COLOT, lcd.BLACK)

############################
# Main loop
############################

info = b""
while(True):
    img = sensor.snapshot()

    code = kpu.run_yolo2(task, img)
    info = b""
    if code:
        for i in code:
            print(i)
            x, y, w, h = i.rect()
            x += w//2
            y += h//2
            x = clip(x, 0, 255)
            info += i.index().to_bytes(1, 0)
            info += x.to_bytes(1, 0)
            info += y.to_bytes(1, 0)
            info += w.to_bytes(1, 0)
            info += h.to_bytes(1, 0)
            info += int(i.value()*255).to_bytes(1, 0)
            a = img.draw_rectangle(i.rect())
    a = lcd.display(img)
    img = img.compress()
    print(bytearray(img))
a = kpu.deinit(task)

sock.close()
