from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import DetectorSubordinate, Experiment, Box

from threading import *
import numpy as np

from django.utils import timezone
import datetime


def exp_list(request):
    if "subordinate" in request.POST.keys():
        subordinate = DetectorSubordinate.objects.filter(name=request.POST['subordinate']).get()
        exp = Experiment.objects.filter(id=request.POST['exp']).get()
        exp.subordinate = subordinate
        exp.save()
        return redirect('exp:list')

    online_exp_list = Experiment.objects.filter(subordinate__isnull=False).order_by('id')
    exp_list = Experiment.objects.filter(subordinate__isnull=True).order_by('id')
    paginator = Paginator(exp_list, 25) # Show 25 contacts per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    subordinates = DetectorSubordinate.objects.filter(experiment__isnull=True)

    return render(request, 'live_experiment/exp_list.html', locals())


def add_box(subordinate_name, x, y, w, h, trk_id):
    if not DetectorSubordinate.objects.filter(name=subordinate_name).exists():
        subordinate = DetectorSubordinate.objects.create(lastTime=datetime.datetime.now(
            tz=timezone.utc))
        subordinate.name = subordinate_name
    else:
        subordinate = DetectorSubordinate.objects.get(name=subordinate_name)
    now = datetime.datetime.now(tz=timezone.utc)
    subordinate.lastTime = now
    subordinate.save()
    for exp in Experiment.objects.filter(subordinate=subordinate).all():
        Box.objects.create(exp=exp, x=np.clip(x, 0, 319), y=np.clip(y, 0, 239), w=w, h=h, trk_id=trk_id)


def add_img(subordinate_name, image_bytes):
    if not DetectorSubordinate.objects.filter(name=subordinate_name).exists():
        subordinate = DetectorSubordinate.objects.create(lastTime=datetime.datetime.now(
            tz=timezone.utc))
        subordinate.name = subordinate_name
    else:
        subordinate = DetectorSubordinate.objects.get(name=subordinate_name)
    for exp in Experiment.objects.filter(subordinate=subordinate).all():
        exp.previewImage.save(str(datetime.datetime.now())+'.jpg', ContentFile(image_bytes))


def add_data(request):
    subordinate_name = request.GET["subordinate_name"]
    x = request.GET["x"]
    y = request.GET["y"]
    w = request.GET["w"]
    h = request.GET["h"]
    trk_id = request.GET["trk_id"]
    add_box(subordinate_name, x, y, w, h, trk_id)

    html = "<html><body>Saved.</body></html>"
    return HttpResponseRedirect()

def stop_exp(request, exp_id):
    exp = Experiment.objects.get(id=exp_id)
    exp.subordinate = None
    exp.save()
    return redirect('exp:list')

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
    heatmap_data = np.zeros((40, 30))
    last_pos = []
    if not boxes.exists():
        return render(request, 'live_experiment/exp.html', locals())
    begin_time = boxes.earliest('time').time
    end_time = boxes.latest('time').time
    bins = 50
    speed_distribution_data = [0 for i in range(bins)]
    dt_data = []
    for box in boxes:
        dt = 0
        if last_pos:
            dt = box.time.timestamp() - last_pos[2]
            v = ((box.x - last_pos[0])**2 + (box.y - last_pos[1])**2)**0.5 / dt
            heatmap_data[int(box.x / 8), int(box.y / 8)] += dt
            speed_data.append([box.time.timestamp() - begin_time.timestamp(), v])
            dt_data.append(dt)
        last_pos = (box.x, box.y, box.time.timestamp())
        coord_data.append([box.x, box.y])
        coord_time_data.append([box.x, box.y, dt])
    speed_array = np.array(speed_data)[..., 1]
    
    # Remove inconsistent detections
    max_speed = np.percentile(speed_array, 99)
    speed_array[speed_array>max_speed] = max_speed

    # Smooth speed
    speed_array = np.convolve(speed_array, [0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05], mode='same')
    speed_data = [[t[0], v] for t, v in zip(speed_data, speed_array)]
    for (t, v), dt_data in zip(speed_data, dt_data):
        if int(v / max_speed * bins) < bins:
            speed_distribution_data[int(v / max_speed * bins)] += dt

    speed_distribution_data = [[
        i / bins * max_speed, speed_distribution_data[i]
    ] for i in range(bins)]

    heatmap_max = heatmap_data.max()
    heatmap_xData = list(range(40))
    heatmap_yData = list(range(30))
    heatmap_data = [[i, j, heatmap_data[i, j]] for i in heatmap_xData
                    for j in heatmap_yData]


    duration = end_time - begin_time
    return render(request, 'live_experiment/exp.html', locals())


def socket_daemon():
    import socket

    def client_thread(conn):
        subordinate_name = conn.recv(10240).decode()
        picture_buffer = b""
        print("Name: " + subordinate_name)
        while True:
            data = conn.recv(10240)
            if data.startswith(b"Detections: "):
                data = np.frombuffer(data[12:], dtype=np.uint16).reshape(-1, 6)
                d = data[data[..., -1].argmax()]
                trk_id, x, y, w, h, score = d
                add_box(subordinate_name, x, y, w, h, trk_id)
                print(data)
                if picture_buffer:
                    add_img(subordinate_name, picture_buffer)
                picture_buffer = b""
            elif data.startswith(b"\xff\xd8\xff\xe0"):
                if picture_buffer:
                    add_img(subordinate_name, picture_buffer)
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
