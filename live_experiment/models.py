from django.db import models
import os


class DetectorSlave(models.Model):
    name = models.TextField(default="Untitled")
    createTime = models.DateTimeField(auto_now_add=True)
    lastTime = models.DateTimeField()

    def __str__(self):
        return self.name


class RegionOfInterest(models.Model):
    name = models.TextField()

    x1 = models.FloatField()
    y1 = models.FloatField()
    x2 = models.FloatField()
    y2 = models.FloatField()

    def __str__(self):
        return self.name
    
    def include(self, x, y):
        return self.x1 < x < self.x2 and self.y1 < y < self.y2
    
    def rect_data(self):
        return [[self.x1, self.y1], [self.x2, self.y1], [self.x2, self.y2], [self.x1, self.y2], [self.x1, self.y1]]


class Experiment(models.Model):
    name = models.TextField(default="Untitled")
    createTime = models.DateTimeField(auto_now_add=True)
    slave = models.ForeignKey(DetectorSlave, on_delete=models.SET_NULL, null=True, blank=True)
    previewImage = models.ImageField(upload_to="previewImg/%Y/%m/%d", blank=True)
    region_of_interests = models.ManyToManyField(RegionOfInterest, blank=True)

    def state(self):
        return "running" if self.slave else "waiting"
    
    def __str__(self):
        return self.name


class Box(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    exp = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    w = models.FloatField()
    h = models.FloatField()
    trk_id = models.IntegerField()
