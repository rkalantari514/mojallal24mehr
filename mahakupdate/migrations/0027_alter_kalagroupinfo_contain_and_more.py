# Generated by Django 5.1.2 on 2024-11-11 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0026_kalagroupinfo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kalagroupinfo',
            name='contain',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='شامل باشد'),
        ),
        migrations.AlterField(
            model_name='kalagroupinfo',
            name='not_contain',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='شامل نباشد'),
        ),
    ]