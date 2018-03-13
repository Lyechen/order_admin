# Generated by Django 2.0 on 2018-03-09 14:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_auto_20180305_2002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnsDeal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('is_deal', models.IntegerField(choices=[(1, '未处理'), (2, '已处理')], default=1, help_text='是否处理', verbose_name='是否处理')),
                ('remarks', models.TextField(default='', help_text='客户备注', verbose_name='客户备注')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '订单退货处理',
                'verbose_name_plural': '订单退货处理',
            },
        ),
        migrations.RemoveField(
            model_name='orderreturns',
            name='order',
        ),
        migrations.AddField(
            model_name='orderreturns',
            name='order_sn',
            field=models.CharField(default='', help_text='订单号', max_length=17, verbose_name='订单号'),
        ),
        migrations.AlterField(
            model_name='abnormalorder',
            name='abnormal_type',
            field=models.IntegerField(choices=[(1, '无货'), (2, '延期'), (3, '退货')], default=1, help_text='异常类型', verbose_name='异常类型'),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='status',
            field=models.IntegerField(choices=[(1, '待支付'), (2, '已取消'), (3, '待接单'), (4, '待发货'), (5, '已发货,配送中'), (6, '已完成'), (8, '申请延期中'), (10, '退款中'), (11, '退货中'), (12, '作废'), (13, '无货'), (14, '退款完成'), (15, '退货完成')], default=1, help_text='订单状态', verbose_name='订单状态'),
        ),
        migrations.AlterField(
            model_name='orderoperationrecord',
            name='status',
            field=models.IntegerField(choices=[(1, '提交订单'), (2, '支付订单'), (3, '取消订单'), (4, '待接单'), (5, '接单'), (6, '发货'), (7, '客户确认收货'), (8, '申请无货'), (9, '确认延期'), (10, '申请延期'), (11, '申请退款'), (12, '申请退货'), (13, '同意退货'), (14, '供应商确认收货'), (15, '确认退款'), (16, '确认无货')], default=1, help_text='订单状态', verbose_name='订单状态'),
        ),
    ]
