# _*_ coding:utf-8 _*_
__author__ = 'jiangchao'
import re
import requests
from rest_framework import serializers
from datetime import timedelta

from .models import Receipt, Order, OrderOperationRecord, OrderDetail, OrderPayment, OrderCancel, OrderLogistics
from .models import OpenReceipt, AbnormalOrder, OrderReturns
from order_admin.settings import ORDER_API_HOST
from utils.log import logger

SUPER_OPERATION = (
    (0, '不操作'),
    (1, '取消订单'),
    (2, '延期发货'),
    (3, '确认收货'),
    (4, '发货'),
    (5, '支付'),
    (6, '无货'),
    (7, '接单')
)


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = "__all__"


class OpenReceiptSerializer(serializers.ModelSerializer):
    images = serializers.CharField(label='URL', allow_null=True, allow_blank=True)

    class Meta:
        model = OpenReceipt
        fields = ['receipt_sn', 'order_sn', 'images', 'remarks']

    def validate(self, attrs):
        images = attrs['images']
        order_sn = attrs['order_sn']
        # 去掉图片url中的域名部分
        regular = '^((http://)|(https://))?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}(/)'
        pattern = re.compile(regular, re.S)
        images = re.sub(pattern, '', images)
        if re.match(r'^/.*', images):
            attrs['images'] = images
        elif images:
            attrs['images'] = '/' + images
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn)
        if not order_detail:
            raise serializers.ValidationError('传入的订单号有误')
        if not order_detail.filter(status__in=[4, 5, 6]):
            raise serializers.ValidationError('当前状态不予许上传发票')
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    # receipt = ReceiptSerializer()
    # number = serializers.IntegerField(required=True, help_text='数量', label='数量')
    # univalent = serializers.FloatField(required=True, help_text='单价', label='单价')

    # data = serializers.CharField(required=True, write_only=True)
    data = serializers.JSONField(binary=False)

    class Meta:
        model = Order
        # fields = ['receipt', 'receiver', 'mobile', 'address', 'goods_name', 'model', 'brand', 'number', 'univalent',
        #           'remarks']
        fields = ['data']

    def validate(self, attrs):
        money = attrs['number'] * attrs['univalent']
        attrs['money'] = money
        url = ORDER_API_HOST + '/order'
        order_sn = requests.post(url)
        attrs['order_sn'] = order_sn
        return attrs


class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderCancelSerializer(serializers.ModelSerializer):
    # order_sn = serializers.CharField()
    guest_id = serializers.IntegerField()

    class Meta:
        model = OrderOperationRecord
        fields = ['order_sn', 'guest_id']

    def validate(self, attrs):
        """后续添加支付接口以及实际情况会相应扩展"""
        order_sn = attrs.get('order_sn', '')
        guest_id = attrs.get('guest_id', 0)
        if not order_sn:
            logger.warning('订单号不能为空!')
            raise serializers.ValidationError('传入订单号不能为空!!!')
        if order_sn.endswith('000000'):
            order = Order.objects.filter(order_sn=order_sn)
            cancel_order = OrderOperationRecord.objects.filter(order_sn=order_sn, status=3)
            # if order:
            #     attrs['id'] = order[0].id
        else:
            order = OrderDetail.objects.filter(son_order_sn=order_sn)
            cancel_order = order.filter(status=2)
        if not order:
            logger.info('传入订单号不存在,请核对!')
            raise serializers.ValidationError('传入订单号不存在!!!')
        if cancel_order:
            logger.info('重复取消订单!')
            raise serializers.ValidationError('无需重复取消订单')
        attrs['guest_id'] = guest_id
        return attrs


class OrderPaymentSerializer(serializers.ModelSerializer):
    trade_no = serializers.CharField(required=True, allow_blank=False)
    order_sn = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = OrderPayment
        fields = ['order_sn', 'trade_no', 'pay_type']

    def validate(self, attrs):
        """验证订单支付信息"""
        order_sn = attrs.get('order_sn', '')
        if not order_sn.endswith('000000'):
            logger.info('传入的订单号[%s],不是母订单' % order_sn)
            raise serializers.ValidationError('传入的订单号[%s],不是母订单' % order_sn)
        order = Order.objects.filter(order_sn=order_sn)
        if not order:
            logger.info('传入的订单号[%s]不存在' % order_sn)
            raise serializers.ValidationError('传入的订单号[%s]不存在' % order_sn)
        has_cancel = OrderDetail.objects.filter(order=order[0].id, status=2)
        if has_cancel:
            logger.info('传入的订单号[%s]已取消不能再支付' % order_sn)
            raise serializers.ValidationError('传入的订单号[%s]已取消不能再支付' % order_sn)
        return attrs


class ReturnsSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=((1, '不操作'), (2, '申请退货'), (3, '确认收货')), label='状态')
    remarks = serializers.CharField(label='备注', allow_blank=True, allow_null=True)

    class Meta:
        model = OrderDetail
        fields = ['status', 'remarks']


class ReturnOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReturns
        fields = ['order_sn', 'receiver', 'mobile', 'address', 'logistics_company', 'logistics_number']


class UserOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = "__all__"


class OrderDelaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ['due_time', 'due_desc']


class AdminOrderCancelSerializer(serializers.ModelSerializer):
    order_sn = serializers.CharField

    class Meta:
        model = OrderCancel
        fields = ['order_sn', 'responsible_party', 'cancel_desc']

    def validate(self, attrs):
        order_sn = attrs.get('order_sn', '')
        if not order_sn:
            logger.info("订单号不能为空")
            raise serializers.ValidationError("订单号不能为空")
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn)
        if not order_detail:
            logger.info("订单号[%s]不存在" % order_sn)
            raise serializers.ValidationError("订单号[%s]不存在" % order_sn)
        return attrs


class SupplierOrderAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = "__all__"


class OrderLogisticsSerializer(serializers.ModelSerializer):
    order_sn = serializers.CharField(max_length=17, label='订单号', required=True)
    logistics_company = serializers.CharField(label='物流公司')
    logistics_number = serializers.CharField(label='物流编号')
    mobile = serializers.CharField(max_length=11, min_length=11, label='电话', allow_null=True, allow_blank=True)
    sender = serializers.CharField(max_length=30, label='送货人', allow_null=True, allow_blank=True)

    class Meta:
        model = OrderLogistics
        fields = ['order_sn', 'mobile', 'logistics_company', 'logistics_number', 'sender']

    def validate(self, attrs):
        """后续验证逻辑可能需要修改"""
        order_sn = attrs['order_sn']
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn, status__in=[4, 11])
        if not order_detail:
            logger.info('订单号[%s]有误或当前状态不是待发货' % order_sn)
            raise serializers.ValidationError('订单号[%s]有误或当前状态不是待发货' % order_sn)
        order = Order.objects.get(pk=order_detail[0].order)
        attrs['receiver'] = order.receiver
        attrs['mobile'] = order.mobile if not attrs.get('mobile', '') else attrs['mobile']
        attrs['address'] = order.province + order.city + order.district + order.address
        attrs['logistics_type'] = 2
        attrs['date_of_delivery'] = (order.add_time + timedelta(
            days=order_detail[0].max_delivery_time)).date()
        return attrs


class AbnormalOrderSerializer(serializers.ModelSerializer):
    expect_date_of_delivery = serializers.DateField(label='预计发货时间', allow_null=True, required=False)

    class Meta:
        model = AbnormalOrder
        fields = ['abnormal_type', 'remarks', 'expect_date_of_delivery', ]

    # def validate(self, attrs):
    #     order_sn = attrs['order_sn']
    #     order_detail = OrderDetail.objects.filter(son_order_sn=order_sn, status=3)
    #     if not order_detail:
    #         logger.info('订单号[%s]有误或当前状态不是待接单' % order_sn)
    #         raise serializers.ValidationError('订单号[%s]有误或当前状态不是待接单' % order_sn)
    #     return attrs


class ChiefUpdateOrderSerializer(serializers.Serializer):
    due_time = serializers.DateField(allow_null=True, label='到期时间')
    due_desc = serializers.CharField(allow_blank=True, allow_null=True, label='到期描述')

    # def validate(self, attrs):
    #     due_time = attrs.get('due_time', '')
    #     due_desc = attrs.get('due_desc', '')
    #     responsible_party = attrs.get('responsible_party', '')
    #     cancel_desc = attrs.get('cancel_desc', '')
    #     if not due_desc and not due_time and not responsible_party and not cancel_desc:
    #         raise serializers.ValidationError('参数不能全部为空')
    #     if due_time and due_desc and (responsible_party or cancel_desc):
    #         raise serializers.ValidationError('参数不能全部为空')
    #     if responsible_party and due_desc and (due_desc or due_time):
    #         raise serializers.ValidationError('参数不能全部为空')
    #     if due_time and due_desc:
    #         is_type = 1
    #     else:
    #         is_type = 2
    #     attrs['is_type'] = is_type
    #     return attrs


class ChiefCancelOrderSerializer(serializers.Serializer):
    responsible_party = serializers.IntegerField(allow_null=True, label='取消订单责任方')
    cancel_desc = serializers.CharField(allow_null=True, label='取消订单描述')

    def validate(self, attrs):
        responsible_party = attrs.get('responsible_party', '')
        if responsible_party not in [1, 2, 3]:
            logger.info('responsible_party参数异常')
            raise serializers.ValidationError('responsible_party参数异常')
        return attrs


class SupplierUpdateOrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=((1, '不操作'), (2, '接单'), (3, '确认收货')))

    class Meta:
        model = OrderDetail
        fields = ['status']


class SuperUserUpdateSerializer(serializers.Serializer):
    is_type = serializers.IntegerField(label='操作类型')
    order_sn = serializers.CharField(label='订单号')
    original_delivery_time = serializers.DateField(label='原发货时间', allow_null=True, required=True)
    expect_date_of_delivery = serializers.DateField(label='预计发货日', allow_null=True, required=True)
    remarks = serializers.CharField(label='备注', allow_null=True, required=True)


class OrderFinanceSerializer(serializers.Serializer):
    order_sn = serializers.CharField(label='订单号')
