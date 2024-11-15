# Generated by Django 5.1.2 on 2024-10-22 22:12

import django_jalali.db.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mahakupdate', '0021_persongroup_alter_kardex_options_person'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kardex',
            options={'ordering': ['-pdate', '-radif'], 'verbose_name': 'کاردکس انبار', 'verbose_name_plural': 'کاردکس های انبار'},
        ),
        migrations.AlterField(
            model_name='kardex',
            name='pdate',
            field=django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ شمسی'),
        ),
    ]
