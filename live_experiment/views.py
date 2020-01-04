from django.http import HttpResponse
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
    html = ""
    for box in Box.objects.filter(exp=exp):
        html += f"{box.trk_id} {box.x} {box.y} {box.w} {box.h}\n"
    return HttpResponse(html)


def client_thread(conn):
    slave_name = conn.recv(10240).decode()
    print(f"Name: {slave_name}")
    while True:
        data = conn.recv(10240)
        data = np.frombuffer(data, dtype=np.uint8).reshape(-1, 5)
        for d in data:
            trk_id, x, y, w, h = d
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
