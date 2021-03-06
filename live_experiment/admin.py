from django.contrib import admin

from RatToolbox import settings
from live_experiment.models import *
from django.urls import reverse


class DetectorSlaveAdmin(admin.ModelAdmin):
    list_display = ('name', 'createTime', 'lastTime')


class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'createTime')
    filter_horizontal = ('region_of_interests',)

    def add_view(self, request, extra_context=None):
        # self.fields = ('name', 'taskType', 'inputVideoFile')
        self.readonly_fields = ('state',)
        return super(ExperimentAdmin, self).change_view(request, extra_context)

    def view_on_site(self, obj):
        url = reverse('exp:detail', args=(obj.id,))
        return url
    #
    # def change_view(self, request, object_id, extra_context=None):
    #     self.fields = ('videoName', 'taskType', 'progress', 'inputVideoFile')
    #     self.readonly_fields = ('taskType', 'createTime', 'progress', 'inputVideoFile')
    #     return super(Experiment, self).change_view(request, object_id)


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(DetectorSlave, DetectorSlaveAdmin)
admin.site.register(RegionOfInterest)
