# Generated by Django 2.0 on 2018-03-01 17:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt', models.IntegerField(help_text='发票ID', verbose_name='发票ID')),
                ('guest_id', models.IntegerField(help_text='客户ID', verbose_name='客户ID')),
                ('order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('receiver', models.CharField(help_text='收货人', max_length=30, verbose_name='收货人')),
                ('mobile', models.CharField(help_text='联系电话', max_length=11, verbose_name='联系电话')),
                ('address', models.CharField(help_text='收货地址', max_length=200, verbose_name='收货地址')),
                ('remarks', models.TextField(default='', help_text='客户备注', verbose_name='客户备注')),
                ('total_money', models.FloatField(blank=True, default=0.0, help_text='订单总额', null=True, verbose_name='订单总额')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '订单',
                'verbose_name_plural': '订单',
            },
        ),
        migrations.CreateModel(
            name='OrderCancel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('responsible_party', models.IntegerField(choices=[(1, '客户'), (2, '供应商'), (3, '平台')], default=1, help_text='责任方', verbose_name='责任方')),
                ('cancel_desc', models.TextField(blank=True, help_text='取消说明', null=True, verbose_name='取消说明')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '取消订单',
                'verbose_name_plural': '取消订单',
            },
        ),
        migrations.CreateModel(
            name='OrderDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(help_text='订单ID', verbose_name='订单ID')),
                ('son_order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('supplier_id', models.IntegerField(help_text='供应商ID', verbose_name='供应商ID')),
                ('goods_id', models.IntegerField(help_text='商品ID', verbose_name='商品ID')),
                ('model', models.CharField(blank=True, default='', help_text='型号', max_length=100, null=True, verbose_name='型号')),
                ('brand', models.CharField(blank=True, default='', help_text='品牌名', max_length=100, null=True, verbose_name='品牌名')),
                ('number', models.IntegerField(blank=True, default=0, help_text='数量', null=True, verbose_name='数量')),
                ('univalent', models.FloatField(blank=True, default=0.0, help_text='单价', null=True, verbose_name='单价')),
                ('subtotal_money', models.FloatField(blank=True, default=0.0, help_text='小计金额', null=True, verbose_name='小计金额')),
                ('price_discount', models.FloatField(default=0.0, help_text='单价优惠', verbose_name='单价优惠')),
                ('delivery_time', models.DateTimeField(blank=True, null=True, verbose_name='发货时间')),
                ('status', models.IntegerField(choices=[(1, '待支付'), (2, '已取消'), (3, '待接单'), (4, '已接单'), (5, '待发货'), (6, '已部分发货'), (7, '已全部发货'), (8, '已完成'), (9, '已确认收货'), (10, '商家申请延期'), (11, '客户申请延期')], default=1, help_text='订单状态', verbose_name='订单状态')),
                ('max_delivery_time', models.IntegerField(blank=True, null=True, verbose_name='最大发货日期')),
                ('due_time', models.DateField(blank=True, null=True, verbose_name='到期时间')),
                ('due_desc', models.TextField(blank=True, null=True, verbose_name='延期说明')),
                ('commission', models.FloatField(blank=True, default=0.0, help_text='佣金', null=True, verbose_name='佣金')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '子订单',
                'verbose_name_plural': '子订单',
            },
        ),
        migrations.CreateModel(
            name='OrderLogistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(help_text='订单ID', verbose_name='订单ID')),
                ('receiver', models.CharField(help_text='收货人', max_length=30, verbose_name='收货人')),
                ('mobile', models.CharField(help_text='联系电话', max_length=11, verbose_name='联系电话')),
                ('address', models.CharField(help_text='收货地址', max_length=200, verbose_name='收货地址')),
                ('logistics_type', models.IntegerField(choices=[(1, '无需物流'), (2, '卖家承担运费'), (3, '买家承担运费')], default=1, help_text='物流方式', verbose_name='物流方式')),
                ('logistics_company', models.CharField(blank=True, default='', help_text='物流公司', max_length=100, null=True, verbose_name='物流公司')),
                ('logistics_number', models.CharField(blank=True, default='', help_text='物流编号', max_length=50, null=True, verbose_name='物流编号')),
                ('date_of_delivery', models.DateField(blank=True, help_text='发货日', null=True, verbose_name='发货日')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '物流单',
                'verbose_name_plural': '物流单',
            },
        ),
        migrations.CreateModel(
            name='OrderOperationRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('status', models.IntegerField(choices=[(1, '提交订单'), (2, '支付订单'), (3, '取消订单'), (4, '待接单'), (5, '接单'), (6, '无货'), (7, '确认延期')], default=1, help_text='订单状态', verbose_name='订单状态')),
                ('operator', models.IntegerField(default=0, help_text='操作员', verbose_name='操作员')),
                ('execution_detail', models.CharField(blank=True, help_text='执行明细', max_length=100, null=True, verbose_name='执行明细')),
                ('progress', models.CharField(blank=True, help_text='当前进度', max_length=30, null=True, verbose_name='当前进度')),
                ('time_consuming', models.FloatField(blank=True, default=0.0, help_text='耗时', null=True, verbose_name='耗时')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '订单操作',
                'verbose_name_plural': '订单操作',
            },
        ),
        migrations.CreateModel(
            name='OrderPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_sn', models.CharField(help_text='订单号', max_length=17, verbose_name='订单号')),
                ('trade_no', models.CharField(blank=True, max_length=100, null=True, verbose_name='交易流水号')),
                ('pay_type', models.IntegerField(choices=[(1, '微信支付'), (2, '支付宝支付'), (3, '银联支付'), (4, '其他方式支付')], default=1, help_text='支付类型', verbose_name='支付类型')),
                ('pay_status', models.IntegerField(choices=[(1, '未支付'), (2, '已支付')], default=1, help_text='订单支付状态', verbose_name='订单支付状态')),
                ('pay_time', models.DateTimeField(blank=True, help_text='支付时间', null=True, verbose_name='支付时间')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '订单支付',
                'verbose_name_plural': '订单支付',
            },
        ),
        migrations.CreateModel(
            name='OrderReturns',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(help_text='订单ID', verbose_name='订单ID')),
                ('returns_sn', models.CharField(help_text='退货单号', max_length=17, verbose_name='退货单号')),
                ('receiver', models.CharField(help_text='收货人', max_length=30, verbose_name='收货人')),
                ('mobile', models.CharField(help_text='联系电话', max_length=11, verbose_name='联系电话')),
                ('address', models.CharField(help_text='收货地址', max_length=200, verbose_name='收货地址')),
                ('logistics_type', models.IntegerField(choices=[(1, '无需物流'), (2, '卖家承担运费'), (3, '买家承担运费')], default=1, help_text='物流方式', verbose_name='物流方式')),
                ('logistics_company', models.CharField(blank=True, default='', help_text='物流公司', max_length=100, null=True, verbose_name='物流公司')),
                ('logistics_number', models.CharField(blank=True, default='', help_text='物流编号', max_length=50, null=True, verbose_name='物流编号')),
                ('date_of_delivery', models.DateField(blank=True, help_text='发货日', null=True, verbose_name='发货日')),
                ('returns_type', models.IntegerField(choices=[(1, '全部退单'), (2, '部分退单')], default=1, help_text='退货类型', verbose_name='退货类型')),
                ('returns_handling_way', models.IntegerField(choices=[(1, '退货入库'), (2, '重新发货'), (3, '不要求归还并重新发货'), (4, '退款'), (5, '不退货并赔偿')], default=1, help_text='退货处理方式', verbose_name='退货处理方式')),
                ('returns_money', models.FloatField(blank=True, default=0.0, help_text='退款金额', null=True, verbose_name='退款金额')),
                ('returns_submit_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='退货申请时间')),
                ('handling_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='退货处理时间')),
                ('returns_reason', models.TextField(default='', help_text='退货理由', verbose_name='退货理由')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '订单退货',
                'verbose_name_plural': '订单退货',
            },
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='', help_text='发票抬头', max_length=150, verbose_name='发票抬头')),
                ('account', models.CharField(default='', help_text='公司账户', max_length=30, verbose_name='公司账户')),
                ('tax_number', models.CharField(default='', help_text='税务编号', max_length=30, verbose_name='税务编号')),
                ('telephone', models.CharField(blank=True, default='', help_text='公司电话', max_length=13, null=True, verbose_name='公司电话')),
                ('bank', models.CharField(default='', help_text='开户行', max_length=30, verbose_name='开户行')),
                ('company_address', models.CharField(default='', help_text='公司地址', max_length=200, verbose_name='公司地址')),
                ('receipt_type', models.IntegerField(choices=[(1, '普通发票'), (2, '增值税发票'), (3, '无需开票')], default=1, help_text='发票类型', verbose_name='发票类型')),
                ('add_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='添加时间')),
            ],
            options={
                'verbose_name': '发票',
                'verbose_name_plural': '发票',
            },
        ),
    ]
