# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2020-06-26 05:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='description',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='\u7b80\u4ecb'),
        ),
    ]
