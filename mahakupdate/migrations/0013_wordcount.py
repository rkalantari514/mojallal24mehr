# Generated by Django 5.1.2 on 2024-10-15 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0012_merge_20241015_1723'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=100, unique=True, verbose_name='کلمه')),
                ('count', models.IntegerField(verbose_name='تعداد')),
            ],
            options={
                'verbose_name': 'تکرار کلمه',
                'verbose_name_plural': 'کلمه',
            },
        ),
    ]