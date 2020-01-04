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

SSID        = "Mouse"
PASSWORD    = "12345678"
MASTER_IP  = "192.168.43.94"
DEVICE_NAME = "001"

fm.register(board_info.WIFI_RX,fm.fpioa.UART2_TX)
fm.register(board_info.WIFI_TX,fm.fpioa.UART2_RX)
uart = machine.UART(machine.UART.UART2,115200,timeout=1000, read_buf_len=4096)
nic=network.ESP8285(uart)
nic.connect(SSID, PASSWORD)

addr = (MASTER_IP, 3456)
sock = socket.socket()
sock.connect(addr)
sock.settimeout(5)

sock.send(b'hello world!')
sock.close()

lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_hmirror(False)

sensor.run(1)
task = kpu.load("/sd/yolo.kmodel")
anchor = (0.750, 0.875, 2.875, 2.500, 2.625, 4.625, 5.625, 2.125, 4.625, 3.625)
a = kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)
while(True):
    img = sensor.snapshot()
    code = kpu.run_yolo2(task, img)
    if code:
        for i in code:
            print(i)
            a = img.draw_rectangle(i.rect())
    a = lcd.display(img)
a = kpu.deinit(task)
