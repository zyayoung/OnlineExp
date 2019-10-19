from django.contrib import admin

from RatToolbox import settings
from task.models import *


class TaskAdmin(admin.ModelAdmin):
    list_display = ('videoName', 'taskType', 'createTime', 'progress')
    list_filter = ('taskType', 'status')
    def add_view(self, request, extra_context=None):   
        self.fields = ('videoName', 'taskType', 'inputVideoFile')    
        self.readonly_fields = tuple()
        return super(TaskAdmin, self).change_view(request, extra_context)
        
    def change_view(self, request, object_id, extra_context=None):   
        self.fields = ('videoName', 'taskType', 'progress', 'inputVideoFile')
        self.readonly_fields = ('taskType', 'createTime', 'progress', 'inputVideoFile')
        return super(TaskAdmin, self).change_view(request, object_id)

admin.site.register(Task, TaskAdmin)
