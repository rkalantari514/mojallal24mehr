# Generated by Django 5.1.2 on 2024-10-26 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0024_merge_20241025_2101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mtables',
            options={'ordering': ['update_priority'], 'verbose_name': 'جدول محک', 'verbose_name_plural': 'جداول محک'},
        ),
        migrations.AddField(
            model_name='mtables',
            name='update_priority',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='اولویت آپدیت'),
        ),
    ]
