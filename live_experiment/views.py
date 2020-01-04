from django.http import HttpResponse
import datetime
from .models import DetectorSlave, Experiment, Box

def add_data(request):
    slave_name = request.GET["slave_name"]
    x = request.GET["x"]
    y = request.GET["y"]
    w = request.GET["w"]
    h = request.GET["h"]
    trk_id = request.GET["trk_id"]

    if not DetectorSlave.objects.filter(name=slave_name).exists():
        slave = DetectorSlave.objects.create(lastTime=datetime.datetime.now())
        slave.name = slave_name
    else:
        slave = DetectorSlave.objects.get(name=slave_name)
    now = datetime.datetime.now()
    slave.lastTime = now
    slave.save()
    for exp in Experiment.objects.filter(slave=slave).all():
        box = Box.objects.create(exp=exp, x=x, y=y, w=w, h=h, trk_id=trk_id)
        box.save()
    html = "<html><body>Saved.</body></html>"
    return HttpResponse(html)


def view_exp(request, exp_id):
    exp = Experiment.objects.get(id=exp_id)
    html = ""
    for box in Box.objects.filter(exp=exp):
        html += f"{box.trk_id} {box.x} {box.y} {box.w} {box.h} {box.time}\n"
    return HttpResponse(html)