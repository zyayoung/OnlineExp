from django.db import models
import os
from RatToolbox.settings import MEDIA_ROOT

class Task(models.Model):
    TASK_TYPES = (
        ("HC", 'Home Cage'),
        ("TV", 'Top View'),
    )
    STATUS_TYPES = (
        ("WT", 'Waiting'),
        ("PR", 'Processing'),
        ("DE", 'Done'),
        ("FE", 'File Format Not Correct'),
    )
    
    videoName = models.TextField(default="Untitled Video")
    createTime = models.DateTimeField(auto_now_add=True)
    taskType = models.CharField(choices=TASK_TYPES, max_length=4, default="HC")
    status = models.CharField(choices=STATUS_TYPES, max_length=4, default="WT")

    # Todo: Set https://docs.djangoproject.com/en/2.0/ref/settings/#std:setting-MEDIA_ROOT
    inputVideoFile = models.FileField(upload_to="inputVideos/%Y/%m/%d")
    previewImage = models.ImageField(upload_to="previewImg/%Y/%m/%d", blank=True)
    outputInfoFile = models.FileField(upload_to="outputInfo/%Y/%m/%d", blank=True)

    is_processing = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)

    total_frames = models.IntegerField(default=-1)
    processed_frames = models.IntegerField(default=0)
    
    def processed(self):
        return self.processed_frames >= self.total_frames
    
    def progress(self):
        if self.status == "PR":
            return "{:d}%".format(self.processed_frames * 100 / self.total_frames)
        else:
            return dict(self.STATUS_TYPES)[self.status]
