# Generated by Django 2.0 on 2018-03-16 11:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0026_orderoperationrecord_remarks'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderoperationrecord',
            name='remarks',
        ),
    ]
