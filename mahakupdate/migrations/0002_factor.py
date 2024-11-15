# Generated by Django 5.0.9 on 2024-10-07 20:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Factor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.IntegerField(default=0, verbose_name='شماره فاکتور')),
                ('pdate', models.CharField(max_length=150, verbose_name='تاریخ شمسی')),
                ('mablagh_factor', models.FloatField(default=0, verbose_name='مبلغ فاکتور')),
                ('takhfif', models.FloatField(default=0, verbose_name='تخفیف')),
                ('create_time', models.TimeField(verbose_name='ساعت ایجاد')),
            ],
            options={
                'verbose_name': 'فاکتور',
                'verbose_name_plural': 'فاکتورها',
            },
        ),
    ]
