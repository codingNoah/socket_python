# Generated by Django 5.0.6 on 2024-06-01 17:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('socket_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reply',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='socket_api.message'),
        ),
    ]
