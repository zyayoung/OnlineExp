# Generated by Django 2.2.5 on 2020-01-08 11:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('live_experiment', '0006_auto_20200108_1913'),
    ]

    operations = [
        migrations.RenameField(
            model_name='experiment',
            old_name='rois',
            new_name='region_of_interests',
        ),
    ]