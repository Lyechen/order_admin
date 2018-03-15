from django.db import models
from django.utils import timezone

# Create your models here.
"""
该模型设计原则:
    将表尽量拆分 尽量做到数据表的 读写业务分离
    直接存ID别用外键关联
"""

"""
待支付
待接单
待发货
已发货
已完成
作废
"""

ORDER_STATUS = (
    (1, '待支付'),
    (2, '已取消'),  # 取消订单
    (3, '待接单'),
    # (4, '已接单'),
    (4, '待发货'),
    (5, '已发货,配送中'),
    (6, '已完成'),
    (8, '申请延期中'),
    (10, '退款中'),
    (11, '退货中'),
    (12, '作废'),
    (13, '无货'),
    (14, '退款完成'),
    (15, '退货完成'),
)

PAYMENT_STATUS = (
    (1, '未支付'),
    (2, '已支付'),
)

OPERATION_STATUS = (
    (1, "提交订单"),
    (2, "支付订单"),
    (3, "取消订单"),
    (4, "待接单"),
    (5, "接单"),
    (6, "发货"),
    (7, "客户确认收货"),
    (8, "申请无货"),
    (9, "确认延期"),
    (10, "申请延期"),
    (11, "系统生成退款单"),
    (12, "申请退货"),
    (13, "同意退货"),
    (14, '供应商确认收货'),
    (15, '确认退款'),
    (16, '确认无货'),
    (17, '填写退货物流'),
)

RECEIPT_TYPE = (
    (1, '普通发票'),
    (2, '增值税发票'),
    (3, '无需开票'),
)

PAY_TYPE = (
    (1, '微信支付'),
    (2, '支付宝支付'),
    (3, '银联支付'),
    (4, '其他方式支付'),
)

LOGISTICS_TYPE = (
    (1, '无需物流'),
    (2, '卖家承担运费'),
    (3, '买家承担运费'),
)

RETURNS_TYPE = (
    (1, '退货'),
    (2, '退款'),
)

RETURNS_HANDLE_WAY = (
    (1, '退货入库'),
    (2, '重新发货'),
    (3, '不要求归还并重新发货'),
    (4, '退款'),
    (5, '不退货并赔偿')
)

RESPONSIBLE_PARTY = (
    (1, '客户'),
    (2, '供应商'),
    (3, '平台'),
)

ABNORMAL_TYPE = (
    (1, '无货'),
    (2, '延期'),
    (3, '退货'),
)

IS_DEAL = (
    (1, '未处理'),
    (2, '已处理'),
)

RETURNS_STATUS = (
    (1, '待收货'),
    (2, '确认收货'),
)

REFUND_STATUS = (
    (1, '等待退款'),
    (2, '退款完成'),
)


class Receipt(models.Model):
    """发票抬头信息"""
    title = models.CharField(max_length=150, verbose_name='发票抬头', help_text='发票抬头', default='')
    account = models.CharField(max_length=30, verbose_name='公司账户', help_text='公司账户', default='')
    tax_number = models.CharField(max_length=30, verbose_name='税务编号', help_text='税务编号', default='')
    telephone = models.CharField(max_length=13, verbose_name='公司电话', null=True, blank=True, help_text='公司电话',
                                 default='')
    bank = models.CharField(max_length=30, verbose_name='开户行', help_text='开户行', default='')
    company_address = models.CharField(max_length=200, verbose_name='公司地址', help_text='公司地址', default='')
    receipt_type = models.IntegerField(choices=RECEIPT_TYPE, default=1, verbose_name='发票类型', help_text='发票类型')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '发票抬头'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class OpenReceipt(models.Model):
    receipt_sn = models.CharField(max_length=30, verbose_name='发票编号', help_text='发票编号')
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    images = models.URLField(verbose_name='发票照片', help_text='发票照片')
    remarks = models.TextField(default='', verbose_name='备注', help_text='备注', null=True, blank=True)
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '开票记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.receipt_sn


class Order(models.Model):
    """订单"""
    receipt = models.IntegerField(verbose_name='发票ID', help_text='发票ID')
    guest_id = models.IntegerField(verbose_name='客户ID', help_text='客户ID')
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    # status = models.IntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', help_text='订单状态')
    receiver = models.CharField(max_length=30, verbose_name='收货人', help_text='收货人')
    mobile = models.CharField(max_length=11, verbose_name='联系电话', help_text='联系电话')
    province = models.CharField(max_length=50, verbose_name='省', help_text='省', default='', blank=True)
    city = models.CharField(max_length=50, verbose_name='市', help_text='市', default='', blank=True)
    district = models.CharField(max_length=50, verbose_name='区', help_text='区', default='', blank=True)
    address = models.CharField(max_length=200, verbose_name='详细地址', help_text='详细地址')
    remarks = models.TextField(default='', verbose_name='客户备注', help_text='客户备注')
    total_money = models.FloatField(default=0.0, null=True, blank=True, verbose_name='订单总额', help_text='订单总额')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class OrderDetail(models.Model):
    """订单详情"""
    order = models.IntegerField(verbose_name='订单ID', help_text='订单ID')
    son_order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    supplier_id = models.IntegerField(verbose_name='供应商ID', help_text='供应商ID')
    goods_id = models.IntegerField(verbose_name='商品ID', help_text='商品ID')
    goods_sn = models.CharField(max_length=17, verbose_name='商品号', help_text='商品号', default='')
    goods_name = models.CharField(max_length=100, verbose_name='商品名', help_text='商品名', default='')
    goods_unit = models.CharField(max_length=10, verbose_name='商品单位', help_text='商品单位', default='')
    supplier_name = models.CharField(max_length=100, verbose_name='供应商名', help_text='供应商名', default='')
    guest_company_name = models.CharField(max_length=100, verbose_name='客户公司名', help_text='客户公司名', default='')
    model = models.CharField(max_length=100, null=True, blank=True, verbose_name='型号', default='', help_text='型号')
    brand = models.CharField(max_length=100, null=True, blank=True, verbose_name='品牌名', default='', help_text='品牌名')
    product_place = models.CharField(max_length=100, null=True, blank=True, verbose_name='产地', default='', help_text='产地')
    # min_buy = models.IntegerField(default=0, verbose_name='起购量', help_text='起购量')
    number = models.IntegerField(default=0, null=True, blank=True, verbose_name='数量', help_text='数量')
    univalent = models.FloatField(default=0.0, null=True, blank=True, verbose_name='单价', help_text='单价')
    subtotal_money = models.FloatField(default=0.0, null=True, blank=True, verbose_name='小计金额', help_text='小计金额')
    price_discount = models.FloatField(default=0.0, verbose_name='单价优惠', help_text='单价优惠')
    delivery_time = models.DateTimeField(null=True, blank=True, verbose_name='发货时间', help_text='发货时间')
    # 该订单状态主要为了方便后续系统查询方便而增加
    status = models.IntegerField(choices=ORDER_STATUS, default=1, verbose_name='订单状态', help_text='订单状态')
    # 最大发货日期
    max_delivery_time = models.IntegerField(null=True, blank=True, verbose_name='最大发货日期', help_text='最大发货日期')
    # 到期时间
    due_time = models.DateField(blank=True, null=True, verbose_name='到期时间', help_text='到期时间')
    # 延期说明
    due_desc = models.TextField(null=True, blank=True, verbose_name='延期说明', help_text='延期说明')
    # 佣金
    commission = models.FloatField(default=0.0, blank=True, null=True, verbose_name='佣金', help_text='佣金')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '子订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.son_order_sn


class OrderPayment(models.Model):
    """订单支付"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    trade_no = models.CharField(max_length=100, null=True, blank=True, verbose_name='交易流水号')
    pay_type = models.IntegerField(choices=PAY_TYPE, default=1, verbose_name='支付类型', help_text='支付类型')
    pay_status = models.IntegerField(choices=PAYMENT_STATUS, default=1, verbose_name='订单支付状态', help_text='订单支付状态')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='支付时间', help_text='支付时间')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单支付'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class OrderCancel(models.Model):
    """取消订单"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    responsible_party = models.IntegerField(choices=RESPONSIBLE_PARTY, default=1, verbose_name='责任方', help_text='责任方')
    cancel_desc = models.TextField(null=True, blank=True, verbose_name='取消说明', help_text='取消说明')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '取消订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class OrderLogistics(models.Model):
    """订单物流表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    receiver = models.CharField(max_length=30, verbose_name='收货人', help_text='收货人')
    mobile = models.CharField(max_length=11, verbose_name='联系电话', help_text='联系电话')
    address = models.CharField(max_length=200, verbose_name='收货地址', help_text='收货地址')
    logistics_type = models.IntegerField(choices=LOGISTICS_TYPE, default=1, verbose_name='物流方式', help_text='物流方式')
    logistics_company = models.CharField(default='', null=True, blank=True, max_length=100, verbose_name='物流公司',
                                         help_text='物流公司')
    logistics_number = models.CharField(default='', null=True, blank=True, max_length=50, verbose_name='物流编号',
                                        help_text='物流编号')
    date_of_delivery = models.DateField(null=True, blank=True, verbose_name='发货日', help_text='发货日')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '物流单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.logistics_number


class OrderOperationRecord(models.Model):
    """订单状态操作记录表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    status = models.IntegerField(choices=OPERATION_STATUS, default=1, verbose_name='订单状态', help_text='订单状态')
    operator = models.IntegerField(default=0, verbose_name='操作员', help_text='操作员')
    execution_detail = models.CharField(blank=True, null=True, max_length=100, verbose_name='执行明细', help_text='执行明细')
    progress = models.CharField(blank=True, null=True, max_length=30, verbose_name='当前进度', help_text='当前进度')
    time_consuming = models.FloatField(blank=True, null=True, verbose_name='耗时', help_text='耗时', default=0.0)
    is_abnormal = models.BooleanField(default=False, verbose_name='是否异常', help_text='是否异常')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单操作'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class OrderReturns(models.Model):
    """订单退货表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号', default='')
    returns_sn = models.CharField(max_length=20, verbose_name='退货单号', help_text='退货单号')
    receiver = models.CharField(max_length=30, verbose_name='收货人', help_text='收货人')
    mobile = models.CharField(max_length=11, verbose_name='联系电话', help_text='联系电话')
    address = models.CharField(max_length=200, verbose_name='收货地址', help_text='收货地址')
    status = models.IntegerField(choices=RETURNS_STATUS, verbose_name='状态', help_text='状态', default=1)
    # logistics_type = models.IntegerField(choices=LOGISTICS_TYPE, default=1, verbose_name='物流方式', help_text='物流方式')
    logistics_company = models.CharField(default='', null=True, blank=True, max_length=100, verbose_name='物流公司',
                                         help_text='物流公司')
    logistics_number = models.CharField(default='', null=True, blank=True, max_length=50, verbose_name='物流编号',
                                        help_text='物流编号')
    # date_of_delivery = models.DateField(null=True, blank=True, verbose_name='发货日', help_text='发货日')
    # returns_type = models.IntegerField(choices=RETURNS_TYPE, default=1, verbose_name='退货类型', help_text='退货类型')
    # returns_handling_way = models.IntegerField(choices=RETURNS_HANDLE_WAY, default=1, verbose_name='退货处理方式',
    #                                            help_text='退货处理方式')
    # returns_money = models.FloatField(default=0.0, null=True, blank=True, verbose_name='退款金额', help_text='退款金额')
    # returns_submit_time = models.DateTimeField(default=timezone.now, verbose_name='退货申请时间')
    # handling_time = models.DateTimeField(default=timezone.now, verbose_name='退货处理时间')
    # returns_reason = models.TextField(default='', verbose_name='退货理由', help_text='退货理由')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单退货'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class OrderRefund(models.Model):
    """订单退款表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号', default='')
    refund_sn = models.CharField(max_length=20, verbose_name='退款单号', help_text='退款单号')
    amount = models.FloatField(default=0.0, verbose_name='退款金额', help_text='退款金额')
    status = models.IntegerField(choices=REFUND_STATUS, verbose_name='状态', help_text='状态', default=1)
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单退款'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class ReturnsDeal(models.Model):
    """退货处理表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    return_type = models.IntegerField(choices=RETURNS_TYPE, default=1, verbose_name='退货类型', help_text='退货类型')
    is_deal = models.IntegerField(choices=IS_DEAL, default=1, verbose_name='是否处理', help_text='是否处理')
    remarks = models.TextField(default='', verbose_name='客户备注', help_text='客户备注')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单退货处理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class AbnormalOrder(models.Model):
    """异常订单"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    abnormal_type = models.IntegerField(choices=ABNORMAL_TYPE, default=1, verbose_name='异常类型', help_text='异常类型')
    remarks = models.TextField(default='', verbose_name='客户备注', help_text='客户备注')
    original_delivery_time = models.DateField(null=True, blank=True, verbose_name='原发货日', help_text='原发货日')
    expect_date_of_delivery = models.DateField(null=True, blank=True, verbose_name='预计发货日', help_text='预计发货日')
    is_deal = models.IntegerField(choices=IS_DEAL, default=1, verbose_name='是否处理', help_text='是否处理')
    responsible_party = models.IntegerField(choices=RESPONSIBLE_PARTY, default=1, verbose_name='责任方', help_text='责任方')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '异常订单'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn


class SuperUserOperation(models.Model):
    """超级管理员操作记录表"""
    order_sn = models.CharField(max_length=17, verbose_name='订单号', help_text='订单号')
    operator = models.IntegerField(verbose_name='操作人', help_text='操作人')
    original_status = models.IntegerField(verbose_name='原状态', help_text='原状态')
    changed_status = models.IntegerField(verbose_name='改变后状态', help_text='改变后状态')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '超级管理员操作'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_sn
