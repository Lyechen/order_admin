# Generated by Django 2.0 on 2018-03-16 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0027_remove_orderoperationrecord_remarks'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderrefund',
            name='return_sn',
            field=models.CharField(default='', help_text='退货单号', max_length=20, verbose_name='退货单号'),
        ),
    ]
