# Generated by Django 2.0 on 2018-03-13 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0019_auto_20180312_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='goods_unit',
            field=models.CharField(default='', help_text='商品单位', max_length=10, verbose_name='商品单位'),
        ),
    ]
