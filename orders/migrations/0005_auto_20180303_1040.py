# Generated by Django 2.0 on 2018-03-03 10:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_auto_20180303_1036'),
    ]

    operations = [
        migrations.RenameField(
            model_name='openreceipt',
            old_name='images',
            new_name='images_url',
        ),
    ]
