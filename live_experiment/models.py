from django.db import models
import os


class DetectorSlave(models.Model):
    name = models.TextField(default="Untitled")
    createTime = models.DateTimeField(auto_now_add=True)
    lastTime = models.DateTimeField()

    def __str__(self):
        return self.name


class Experiment(models.Model):
    name = models.TextField(default="Untitled")
    createTime = models.DateTimeField(auto_now_add=True)
    slave = models.ForeignKey(DetectorSlave, on_delete=models.SET_NULL, null=True, blank=True)
    previewImage = models.ImageField(upload_to="previewImg/%Y/%m/%d", blank=True)

    def state(self):
        return "running" if self.slave else "waiting"


class Box(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    exp = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    w = models.FloatField()
    h = models.FloatField()
    trk_id = models.IntegerField()
