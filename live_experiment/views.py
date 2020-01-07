from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render
from .models import DetectorSlave, Experiment, Box

from threading import *
import numpy as np

from django.utils import timezone
import datetime


def add_box(slave_name, x, y, w, h, trk_id):
    if not DetectorSlave.objects.filter(name=slave_name).exists():
        slave = DetectorSlave.objects.create(lastTime=datetime.datetime.now(
            tz=timezone.utc))
        slave.name = slave_name
    else:
        slave = DetectorSlave.objects.get(name=slave_name)
    now = datetime.datetime.now(tz=timezone.utc)
    slave.lastTime = now
    slave.save()
    for exp in Experiment.objects.filter(slave=slave).all():
        box = Box.objects.create(exp=exp, x=np.clip(x, 0, 319), y=np.clip(y, 0, 239), w=w, h=h, trk_id=trk_id)


def add_img(slave_name, image_bytes):
    if not DetectorSlave.objects.filter(name=slave_name).exists():
        slave = DetectorSlave.objects.create(lastTime=datetime.datetime.now(
            tz=timezone.utc))
        slave.name = slave_name
    else:
        slave = DetectorSlave.objects.get(name=slave_name)
    for exp in Experiment.objects.filter(slave=slave).all():
        exp.previewImage.save(str(datetime.datetime.now())+'.jpg', ContentFile(image_bytes))


def add_data(request):
    slave_name = request.GET["slave_name"]
    x = request.GET["x"]
    y = request.GET["y"]
    w = request.GET["w"]
    h = request.GET["h"]
    trk_id = request.GET["trk_id"]
    add_box(slave_name, x, y, w, h, trk_id)

    html = "<html><body>Saved.</body></html>"
    return HttpResponse(html)


def view_exp(request, exp_id):
    exp = Experiment.objects.get(id=exp_id)
    try:
        image_url = exp.previewImage.url
    except ValueError:
        image_url = "#"
    boxes = Box.objects.filter(exp=exp)
    total_count = len(boxes)
    speed_data = []
    coord_data = []
    coord_time_data = []
    heatmap_data = np.zeros((32, 24))
    last_pos = []
    if not boxes.exists():
        return render(request, 'live_experiment/exp.html', locals())
    begin_time = boxes.earliest('time').time
    end_time = boxes.latest('time').time
    max_speed = 0
    speed_distribution_data = [0 for i in range(100)]
    for box in boxes:
        dt = 0
        if last_pos:
            dt = box.time.timestamp() - last_pos[2]
            v = ((box.x - last_pos[0])**2 + (box.y - last_pos[1])**2)**0.5 / dt
            max_speed = max(v, max_speed)
            heatmap_data[int(box.x / 10), int(box.y / 10)] += dt
            speed_data.append([box.time.timestamp() - begin_time.timestamp(), v])
        last_pos = (box.x, box.y, box.time.timestamp())
        coord_data.append([box.x, box.y])
        coord_time_data.append([box.x, box.y, dt])
    for t, v in speed_data:
        speed_distribution_data[int(v / max_speed * 99)] += 1

    speed_distribution_data = [[
        i / 100 * max_speed, speed_distribution_data[i] / total_count
    ] for i in range(100)]

    heatmap_max = heatmap_data.max()
    heatmap_xData = list(range(32))
    heatmap_yData = list(range(24))
    heatmap_data = [[i, j, heatmap_data[i, j]] for i in heatmap_xData
                    for j in heatmap_yData]


    duration = end_time - begin_time
    return render(request, 'live_experiment/exp.html', locals())


def socket_daemon():
    import socket

    def client_thread(conn):
        slave_name = conn.recv(10240).decode()
        picture_buffer = b""
        print("Name: " + slave_name)
        while True:
            data = conn.recv(10240)
            if data.startswith(b"Detections: "):
                data = np.frombuffer(data[12:], dtype=np.uint16).reshape(-1, 6)
                d = data[data[..., -1].argmax()]
                trk_id, x, y, w, h, score = d
                add_box(slave_name, x, y, w, h, trk_id)
                print(data)
                if picture_buffer:
                    add_img(slave_name, picture_buffer)
                picture_buffer = b""
            elif data.startswith(b"\xff\xd8\xff\xe0"):
                if picture_buffer:
                    add_img(slave_name, picture_buffer)
                picture_buffer = data
            else:
                picture_buffer += data

    HOST = '0.0.0.0'  # Symbolic name meaning all available interfaces
    PORT = 3456  # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(10)
    while 1:
        conn, addr = s.accept()
        print('Connected with ' + addr[0] + ':' + str(addr[1]))

        t = Thread(target=client_thread, args=(conn, ), daemon=True)
        t.start()


socket_daemon_thread = Thread(target=socket_daemon, daemon=True)
socket_daemon_thread.start()
