from django.http import HttpResponse
from django.shortcuts import render
from .models import DetectorSlave, Experiment, Box

from threading import *
import numpy as np

from django.utils import timezone
import datetime


def add_box(slave_name, x, y, w, h, trk_id):
    if not DetectorSlave.objects.filter(name=slave_name).exists():
        slave = DetectorSlave.objects.create(lastTime=datetime.datetime.now(tz=timezone.utc))
        slave.name = slave_name
    else:
        slave = DetectorSlave.objects.get(name=slave_name)
    now = datetime.datetime.now(tz=timezone.utc)
    slave.lastTime = now
    slave.save()
    for exp in Experiment.objects.filter(slave=slave).all():
        box = Box.objects.create(exp=exp, x=x, y=y, w=w, h=h, trk_id=trk_id)
        # box.save()


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
    boxes = Box.objects.filter(exp=exp)
    speed_data = []
    coord_data = []
    last_pos = None
    for box in boxes:
        if last_pos:
            v = ((box.x-last_pos[0])**2+(box.y-last_pos[1])**2)**0.5 / (box.time.timestamp() - last_pos[2])
            speed_data.append([box.time.timestamp(), v])
        last_pos = (box.x, box.y, box.time.timestamp())
        coord_data.append([box.x, box.y])
    return render(request, 'live_experiment/exp.html', locals())


def client_thread(conn):
    slave_name = conn.recv(10240).decode()
    print("Name: "+slave_name)
    while True:
        data = conn.recv(10240)
        data = np.frombuffer(data, dtype=np.uint8).reshape(-1, 6)
        d = data[data[..., -1].argmax()]
        trk_id, x, y, w, h, score = d
        add_box(slave_name, x, y, w, h, trk_id)
        # upload_thread = Thread(target=add_box, args=(slave_name, x, y, w, h, trk_id), daemon=True)
        # upload_thread.start()
        print(data)


def socket_daemon():
    import socket

    HOST = '0.0.0.0'  # Symbolic name meaning all available interfaces
    PORT = 3456  # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(10)
    while 1:
        conn, addr = s.accept()
        print('Connected with ' + addr[0] + ':' + str(addr[1]))

        t = Thread(target=client_thread, args=(conn,), daemon=True)
        t.start()

socket_daemon_thread = Thread(target=socket_daemon, daemon=True)
socket_daemon_thread.start()
