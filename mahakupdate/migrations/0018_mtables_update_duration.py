# Generated by Django 5.1.2 on 2024-10-18 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0017_mtables_last_update_time_mtables_update_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='mtables',
            name='update_duration',
            field=models.FloatField(blank=True, null=True, verbose_name='مدت زمان به\u200cروزرسانی (ثانیه)'),
        ),
    ]
