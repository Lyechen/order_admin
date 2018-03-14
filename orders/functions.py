# _*_ coding:utf-8 _*_
__author__ = 'jiangchao'

import re
import json
import requests
import time

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime, timedelta
from django.forms.models import model_to_dict

from .serializers import OrderSerializer, OrderDetailSerializer, OrderCancelSerializer, OrderPaymentSerializer
from .serializers import UserOrderSerializer, OrderDelaySerializer, AdminOrderCancelSerializer
from .serializers import SupplierOrderAdminSerializer, OrderLogisticsSerializer, ReceiptSerializer
from .serializers import OpenReceiptSerializer, AbnormalOrderSerializer, ChiefUpdateOrderSerializer
from .serializers import SupplierUpdateOrderSerializer, SuperUserUpdateSerializer
from .models import Order, Receipt, OrderDetail, OrderLogistics, OrderOperationRecord, OrderPayment, OrderCancel
from .models import OpenReceipt, AbnormalOrder, SuperUserOperation, ReturnsDeal, OrderReturns, OrderRefund
from order_admin.settings import ORDER_API_HOST
from utils.log import logger
from utils.string_extension import safe_int
from utils.http import APIResponse, CONTENT_RANGE, CONTENT_TOTAL, get_limit
from order_admin.settings import CDN_HOST

RECEIPT_TYPE = {
    1: "普通发票",
    2: "增值税发票",
    3: "无需发票",
    '普通发票': 1,
    '增值税发票': 2,
    '无需发票': 3,
}

ORDER_STATUS = {
    1: '待支付',
    2: '已取消',  # 未支付取消订单
    3: '待接单',
    # 4: '已接单',
    4: '待发货',
    5: '已发货',
    # 6: '已确认收货',
    6: '已完成',
    8: '申请延期',
    # 9: '确认延期',
    10: '退款中',
    11: '退货',
    12: '作废',
    13: '无货',
    '待支付': 1,
    '已取消': 2,  # 未支付取消订单
    '待接单': 3,
    '待发货': 4,
    '已发货': 5,
    # '已确认收货': 6,
    '已完成': 6,
    '申请延期': 8,
    # '确认延期': 9,
    '退款': 10,
    '退货': 11,
    '作废': 12,
    '无货': 13,
}

PAY_STATUS = {
    1: '未支付',
    2: '已支付',
    '未支付': 1,
    '已支付': 2,
}

PAY_TYPE = {
    1: '微信支付',
    2: '支付宝支付',
    3: '银联支付',
    4: '其他方式支付',
    '微信支付': 1,
    '支付宝支付': 2,
    '银联支付': 3,
    '其他方式支付': 4,
}

OPERATIONS = {
    1: "提交订单",
    2: "支付订单",
    3: "取消订单",
    4: "待接单",
    5: "接单",
    6: "发货",
    7: "确认收货",
    8: "无货",
    9: "确认延期",
    '提交订单': 1,
    '支付订单': 2,
    '取消订单': 3,
    '待接单': 4,
    '接单': 5,
    '发货': 6,
    '确认收货': 7,
    '无货': 8,
    '确认延期': 9,
}

# 超级管理员动作类型定义
IS_TYPE = {
    1: '取消订单',
    2: '延期发货',
    3: '确认收货',
    4: '发货',
    5: '支付',
    6: '无货',
    7: '接单',
}


def generation_order(data):
    data = re.sub('\'', '\"', data)
    now = datetime.now()
    date = now.date()
    delta = timedelta(days=15)
    due_time = date + delta
    try:
        data = json.loads(data)
        # 发票信息
        if data[0]['receipt_type'] == 3:
            receipt = Receipt.objects.create(receipt_type=data[0]['receipt_type'])
        else:
            receipt = Receipt.objects.create(
                title=data[0]['title'],
                account=data[0]['account'],
                tax_number=data[0]['tax_number'],
                telephone=data[0]['telephone'],
                bank=data[0]['bank'],
                company_address=data[0]['company_address'],
                receipt_type=data[0]['receipt_type'],
            )
        # 收货人
        receiver = data[0]['receiver']
        # 电话
        mobile = data[0]['mobile']
        # 收货地址
        address = data[0]['address']
        # 备注
        remarks = data[0]['remarks']
        # 买家ID
        guest_id = data[0]['guest_id']
        # 这里后续需要加上获取佣金比例的逻辑 暂时先用 0.0 替代
        ratio = 0.0
        order_status = 1
        headers = {'content-type': 'application/json',
                   'user-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
        parameters = json.dumps({})
        try:
            response = requests.post(ORDER_API_HOST + '/api/order', data=parameters, headers=headers)
            response_dict = json.loads(response.text)
        except Exception as e:
            logger.info('ID生成器连接失败!!!')
            response = APIResponse(success=False, data={}, msg='ID生成器连接失败!!!')
            return response
        # 母订单号
        mother_order_sn = response_dict['data']['order_sn']
        # 创建母订单信息, 母订单类型订单不存在母订单
        mother_order = Order.objects.create(receipt=receipt.id, remarks=remarks, receiver=receiver, mobile=mobile,
                                            guest_id=guest_id, order_sn=mother_order_sn, address=address)
        # 增加母订单状态信息
        OrderOperationRecord.objects.create(order_sn=mother_order.order_sn, status=1, operator=guest_id,
                                            execution_detail='提交订单', progress='未支付')
        # 增加初始订单支付信息
        OrderPayment.objects.create(order_sn=mother_order_sn, pay_status=1)
        total_money = 0.0
        for _data in data:
            parameters = json.dumps({'order_id': mother_order_sn})
            response = requests.post(ORDER_API_HOST + '/api/order', data=parameters, headers=headers)
            order_sn = json.loads(response.text)['data']['order_sn']
            price_discount = float(_data.get('price_discount', 0.0))
            subtotal_money = float(_data['univalent']) * float(_data['number']) * (1.0 - price_discount)
            total_money += subtotal_money
            _order = OrderDetail.objects.create(
                order=mother_order.id,
                son_order_sn=order_sn,
                supplier_id=_data['supplier_id'],
                goods_id=_data['goods_id'],
                model=_data['model'],
                brand=_data['brand'],
                number=int(_data['number']),
                univalent=float(_data['univalent']),
                subtotal_money=subtotal_money,
                commission=subtotal_money * ratio,
                price_discount=price_discount,
                status=order_status,
                max_delivery_time=_data['max_delivery_time'],
                due_time=due_time
            )
            # 增加子订单状态信息
            OrderOperationRecord.objects.create(order_sn=_order.son_order_sn, status=1, operator=guest_id,
                                                execution_detail='用户[%s]提交订单' % guest_id, progress='未支付')
            OrderPayment.objects.create(order_sn=_order.son_order_sn, pay_status=1)
        mother_order.total_money = total_money
        mother_order.save()
    except json.JSONDecodeError as e:
        logger.info("{msg: 请求参数异常}")
        response = APIResponse(success=False, data={}, msg='请求参数异常')
        return response
    result = {
        'id': mother_order.id,
        'mother_order_sn': mother_order_sn,
        'add_time': mother_order.add_time,
        'address': mother_order.address,
        'receipt_title': data[0]['title'],
        'receipt_type': RECEIPT_TYPE[receipt.receipt_type],
        'status': ORDER_STATUS[order_status]
    }
    response = APIResponse(success=True, data=result, msg='创建订单信息成功')
    return response


def get_son_order_detail(instance, guest_id):
    data = []
    _instance = instance
    instance = Order.objects.filter(pk=instance.order)
    if instance[0].guest_id != int(guest_id):
        response = APIResponse(success=False, data={})
        return response
    result = {}
    receipt = Receipt.objects.get(pk=instance[0].receipt)
    result['receipt_title'] = receipt.title
    result['account'] = receipt.account
    result['tax_number'] = receipt.tax_number
    result['telephone'] = receipt.telephone
    result['bank'] = receipt.bank
    result['company_address'] = receipt.company_address
    result['receipt_type'] = receipt.receipt_type
    result['guest_id'] = instance[0].guest_id
    result['total_money'] = instance[0].total_money
    result['add_time'] = instance[0].add_time.date()
    now = datetime.now()
    delta = timedelta(days=7)
    count_down = instance[0].add_time + delta - now
    result['order_sn'] = instance[0].order_sn
    result['count_down'] = count_down
    sub_order = []
    __dict = {}
    abnormal_delay_order = AbnormalOrder.objects.filter(order_sn=_instance.son_order_sn,
                                                        abnormal_type=2,
                                                        is_deal=2)
    abnormal_no_order = AbnormalOrder.objects.filter(order_sn=_instance.son_order_sn,
                                                     abnormal_type=1,
                                                     is_deal=2)
    if not abnormal_delay_order and _instance.status == 8:
        _status = '待接单'
    elif not abnormal_no_order and _instance.status == 13:
        _status = '待接单'
    else:
        _status = ORDER_STATUS[_instance.status]
    pay_status = OrderPayment.objects.filter(order_sn=_instance.son_order_sn).order_by('-add_time')[
        0].pay_status
    __dict['son_order_sn'] = _instance.son_order_sn
    __dict['number'] = _instance.number
    __dict['univalent'] = _instance.univalent
    __dict['max_delivery_time'] = _instance.max_delivery_time
    __dict['order_status'] = _status
    __dict['pay_status'] = PAY_STATUS[pay_status]
    sub_order.append(__dict)
    result['sub_order'] = sub_order
    data.append(result)
    response = APIResponse(success=True, data=data)
    return response


def get_mother_order_detail(instance, serializer):
    result = serializer.data
    receipt = Receipt.objects.get(pk=serializer.data['receipt'])
    result['receipt_title'] = receipt.title
    result['account'] = receipt.account
    result['tax_number'] = receipt.tax_number
    result['telephone'] = receipt.telephone
    result['bank'] = receipt.bank
    result['company_address'] = receipt.company_address
    result['receipt_type'] = receipt.receipt_type
    order_detail = OrderDetail.objects.filter(order=int(instance.id))
    sub_order = []
    for _order in order_detail:
        _sub_order = {}
        abnormal_delay_order = AbnormalOrder.objects.filter(order_sn=_order.son_order_sn,
                                                            abnormal_type=2,
                                                            is_deal=2)
        abnormal_no_order = AbnormalOrder.objects.filter(order_sn=_order.son_order_sn,
                                                         abnormal_type=1,
                                                         is_deal=2)
        if not abnormal_delay_order and _order.status == 8:
            _status = '待接单'
        elif not abnormal_no_order and _order.status == 13:
            _status = '待接单'
        else:
            _status = ORDER_STATUS[_order.status]
        _sub_order['id'] = _order.id
        _sub_order['order_sn'] = _order.son_order_sn
        _sub_order['supplier_id'] = _order.supplier_id
        _sub_order['goods_id'] = _order.goods_id
        _sub_order['model'] = _order.model
        _sub_order['brand'] = _order.brand
        _sub_order['status'] = _status
        _sub_order['number'] = _order.number
        _sub_order['univalent'] = _order.univalent
        _sub_order['price_discount'] = _order.price_discount
        _sub_order['delivery_time'] = _order.delivery_time
        _sub_order['add_time'] = _order.add_time
        sub_order.append(_sub_order)
        # 优化方法
        # sub_order.append(model_to_dict(_order))
    result['sub_order'] = sub_order
    response = APIResponse(data=result, success=True)
    return response


def get_user_order_list(orders, count, is_all=False):
    data = []
    for order in orders:
        _dict = {}
        receipt = Receipt.objects.get(pk=order.receipt)
        _dict['mother_order_id'] = order.id
        _dict['receipt_title'] = receipt.title
        _dict['account'] = receipt.account
        _dict['tax_number'] = receipt.tax_number
        _dict['telephone'] = receipt.telephone
        _dict['bank'] = receipt.bank
        _dict['company_address'] = receipt.company_address
        _dict['receipt_type'] = receipt.receipt_type
        _dict['guest_id'] = order.guest_id
        _dict['order_sn'] = order.order_sn
        _dict['receiver'] = order.receiver
        _dict['mobile'] = order.mobile
        _dict['total_money'] = order.total_money
        _dict['remarks'] = order.remarks
        _dict['address'] = order.address
        order_details = OrderDetail.objects.filter(order=order.id,
                                                   status__in=[1, 3, 4, 5, 6, 8, 10, 11, 12, 13, 14, 15])
        _dict['type_count'] = count
        if not is_all:
            order_details = order_details[:1]
        result = []
        for order_detail in order_details:
            __dict = {}
            __dict['son_order_id'] = order_detail.id
            __dict['son_order_sn'] = order_detail.son_order_sn
            __dict['supplier_id'] = order_detail.supplier_id
            __dict['goods_id'] = order_detail.goods_id
            __dict['model'] = order_detail.model
            __dict['brand'] = order_detail.brand
            __dict['number'] = order_detail.number
            __dict['univalent'] = order_detail.univalent
            __dict['subtotal_money'] = order_detail.subtotal_money
            __dict['price_discount'] = order_detail.price_discount
            __dict['delivery_time'] = order_detail.delivery_time
            __dict['status'] = order_detail.status
            __dict['max_delivery_time'] = order_detail.max_delivery_time
            result.append(__dict)
        _dict['sub_order'] = result
        data.append(_dict)
    return data


def payment_order(serializer, guest_id):
    trade_no = serializer.data['trade_no']
    pay_type = serializer.data['pay_type']
    order_sn = serializer.data['order_sn']
    order = Order.objects.get(order_sn=order_sn)
    orders = OrderDetail.objects.filter(order=order.id, status=1)
    OrderPayment.objects.create(order_sn=order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
    OrderOperationRecord.objects.create(order_sn=order_sn, status=2, operator=guest_id,
                                        execution_detail='用户[%s]对订单[%s]执行支付操作,使用[%s]方式支付' % (
                                            guest_id, order_sn, PAY_TYPE[pay_type]), progress='已支付')
    for order in orders:
        # OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=2, operator=guest_id,
        #                                     execution_detail=PAY_TYPE[pay_type], progress='已支付')
        # # 创建一条系统记录
        # OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=4, operator=0,
        #                                     execution_detail='接单提醒', progress='已支付')
        OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=2, operator=guest_id,
                                            execution_detail='用户[%s]对订单[%s]执行支付操作,使用[%s]方式支付' % (
                                                guest_id, order.son_order_sn, PAY_TYPE[pay_type]), progress='已支付')
        OrderPayment.objects.create(order_sn=order.son_order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
        order.status = 3
        order.save()
    response = APIResponse(data={}, success=True, msg='订单支付状态修改成功')
    return response


def returns_order(instance, status, guest_id, remarks):
    if not isinstance(instance, OrderDetail):
        response = APIResponse(success=False, data={})
        return response
    if status == 2:
        # 状态
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=instance.son_order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=12, operator=guest_id,
                                            execution_detail='用户[%s]对订单[%s]执行申请退货操作' % (
                                                guest_id, instance.son_order_sn), progress='已支付',
                                            time_consuming=time_consuming)
        try:
            return_order = ReturnsDeal.objects.get(order_sn=instance.son_order_sn)
            return_order.is_deal = 1
            return_order.return_type = 1
            return_order.remarks = remarks
            return_order.save()
        except Exception as e:
            ReturnsDeal.objects.create(order_sn=instance.son_order_sn, is_deal=1, remarks=remarks, return_type=1)
        instance.status = 11
        instance.save()
        response = APIResponse(success=True, data={}, msg='退货申请提交成功等待审核')
        return response
    else:
        response = APIResponse(success=False, data={})
        return response


def get_chief_order(order_details, is_abnormal=False):
    result = []
    for _order in order_details:
        __dict = {}
        order = Order.objects.get(pk=_order.order)
        __dict['id'] = _order.id
        __dict['guest_name'] = order.guest_id
        __dict['order_sn'] = order.order_sn
        __dict['receiver'] = order.receiver
        __dict['mobile'] = order.mobile
        __dict['address'] = order.address
        __dict['remarks'] = order.remarks
        __dict['total_money'] = order.total_money
        if is_abnormal:
            # 异常的逻辑处理
            order_operations = OrderOperationRecord.objects.filter(order_sn=_order.son_order_sn, status__in=[5, 6])
            __dict['is_taking'] = 1 if order_operations.filter(status=6) else 0
            __dict['is_delivery'] = 1 if order_operations.filter(status=5) else 0
            abnormal = AbnormalOrder.objects.filter(order_sn=_order.son_order_sn)
            # 1: 无货  2: 延期
            __dict['abnormal_tag'] = 1 if abnormal.filter(abnormal_type=1) else 2
            # 1: 未处理  2: 处理
            __dict['is_deal'] = 1 if abnormal.filter(is_deal=1) else 0
            # 1 客户  2 供应商  3 平台
            __dict['responsible_party'] = abnormal[0].responsible_party
            __dict['abnormal_add_time'] = int(abnormal[0].add_time.timestamp())
        payment = OrderPayment.objects.filter(order_sn=_order.son_order_sn).order_by('-add_time')
        __dict['son_order_sn'] = _order.son_order_sn
        __dict['supplier_name'] = _order.supplier_id
        __dict['goods_id'] = _order.goods_id
        __dict['model'] = _order.model
        __dict['number'] = _order.number
        __dict['order_status'] = _order.status
        __dict['univalent'] = _order.univalent
        __dict['price_discount'] = _order.price_discount
        __dict['max_delivery_time'] = _order.max_delivery_time
        __dict['pay_status'] = payment[0].pay_status
        __dict['commission'] = _order.commission
        __dict['add_time'] = int(_order.add_time.timestamp())
        result.append(__dict)
    return result


def deal_supplier_operation(abnormal_type, order_sn, original_delivery_time,
                            expect_date_of_delivery, operator, serializer, remarks):
    # 无货
    if abnormal_type == 1:
        order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=order_sn, status=8,
                                            operator=operator,
                                            execution_detail='供应商[%s]执行订单[%s]申请无货操作' %
                                                             (order_detail.supplier_id, order_sn),
                                            progress='待接单,无货', time_consuming=time_consuming, is_abnormal=True)
        try:
            abnormal_order = AbnormalOrder.objects.get(order_sn=order_sn, abnormal_type=1)
            abnormal_order.is_deal = 1
            abnormal_order.remarks = remarks
            abnormal_order.save()
        except Exception as e:
            AbnormalOrder.objects.create(order_sn=order_sn, abnormal_type=1, remarks=remarks, is_deal=1)
        order_detail.status = 13
        order_detail.save()
    else:
        order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
        expect_date_of_delivery = datetime.strptime(expect_date_of_delivery, '%Y-%m-%d')
        original_delivery_time = datetime.strptime(original_delivery_time, '%Y-%m-%d')
        if expect_date_of_delivery < original_delivery_time:
            response = APIResponse(success=False, data={}, msg='传入的时间有误')
            return response
        order_detail.max_delivery_time = (expect_date_of_delivery - original_delivery_time).days
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=order_sn, status=10,
                                            operator=operator,
                                            execution_detail='供应商[%s]执行订单[%s]申请延期操作' %
                                                             (order_detail.supplier_id, order_sn),
                                            progress='申请延期', time_consuming=time_consuming, is_abnormal=True)
        try:
            abnormal_order = AbnormalOrder.objects.get(order_sn=order_sn, abnormal_type=2)
            abnormal_order.remarks = remarks
            abnormal_order.is_deal = 1
            abnormal_order.remarks = remarks
            abnormal_order.original_delivery_time = original_delivery_time
            abnormal_order.expect_date_of_delivery = expect_date_of_delivery
            abnormal_order.save()
        except Exception as e:
            AbnormalOrder.objects.create(order_sn=order_sn, abnormal_type=2, remarks=remarks, is_deal=1,
                                         original_delivery_time=original_delivery_time,
                                         expect_date_of_delivery=expect_date_of_delivery)
        order_detail.status = 8
        order_detail.save()
    response = APIResponse(success=True, data={})
    return response


def superuser_get_order_detail(orders, son_id=None):
    data = {}
    order = orders
    data['id'] = order.id
    receipt = Receipt.objects.get(pk=order.receipt)
    data['title'] = receipt.title
    data['account'] = receipt.account
    data['tax_number'] = receipt.tax_number
    data['telephone'] = receipt.telephone
    data['bank'] = receipt.bank
    data['company_address'] = receipt.company_address
    data['receipt_type'] = receipt.receipt_type
    data['add_time'] = receipt.add_time
    data['guest_id'] = order.guest_id
    data['order_sn'] = order.order_sn
    data['receiver'] = order.receiver
    data['mobile'] = order.mobile
    data['address'] = order.address
    data['remarks'] = order.remarks
    data['total_money'] = order.total_money
    order_details = OrderDetail.objects.filter(order=order.id)
    result = []
    if son_id:
        order_details = order_details.filter(pk=son_id)
    for order_detail in order_details:
        __dict = {}
        __dict['son_order_sn'] = order_detail.son_order_sn
        __dict['supplier_id'] = order_detail.supplier_id
        __dict['goods_id'] = order_detail.goods_id
        __dict['model'] = order_detail.model
        __dict['brand'] = order_detail.brand
        __dict['number'] = order_detail.number
        __dict['univalent'] = order_detail.univalent
        __dict['subtotal_money'] = order_detail.subtotal_money
        __dict['price_discount'] = order_detail.price_discount
        __dict['delivery_time'] = order_detail.delivery_time
        __dict['status'] = order_detail.status
        __dict['max_delivery_time'] = order_detail.max_delivery_time
        __dict['commission'] = order_detail.commission
        __dict['due_time'] = order_detail.due_time
        __dict['due_desc'] = order_detail.due_desc
        _result = []
        for operation in OrderOperationRecord.objects.filter(order_sn=order_detail.son_order_sn):
            _dict = {}
            _dict['status'] = operation.status
            _dict['operator'] = operation.operator
            _dict['execution_detail'] = operation.execution_detail
            _dict['progress'] = operation.progress
            _dict['time_consuming'] = operation.time_consuming
            _dict['add_time'] = operation.add_time
            _result.append(_dict)
        payment = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn).order_by('-add_time')[0]
        __dict['pay_status'] = payment.pay_status
        __dict['pay_type'] = payment.pay_type
        __dict['operation'] = _result
        result.append(__dict)
    data['sub_order'] = result
    return data


def deal_returns_order(order_details, returns_status, returns_sn, start_time='', end_time=''):
    data = []
    order_returns = OrderReturns.objects.filter(order_sn__in=[obj.son_order_sn for obj in order_details])
    if returns_sn:
        order_returns = order_returns.filter(returns_sn=returns_sn)
    if returns_status:
        order_returns = order_returns.filter(status=returns_status)
    if start_time:
        start_time += ' 23:59:59'
        order_returns = order_returns.filter(add_time__gte=start_time)
    if end_time:
        end_time += ' 23:59:59'
        order_returns = order_returns.filter(add_time__lte=end_time)
    for order_return in order_returns:
        result = {}
        order_detail = order_details.filter(son_order_sn=order_return.order_sn)
        if not order_detail:
            response = APIResponse(success=False, data={})
            return response
        if not order_return:
            response = APIResponse(success=False, data={}, msg='没有退货申请记录，请联系管理员')
            return response
        order_detail = order_detail[0]
        result['id'] = order_detail.id
        result['order_sn'] = order_detail.son_order_sn
        result['subtotal_money'] = order_detail.subtotal_money
        result['model'] = order_detail.model
        result['brand'] = order_detail.brand
        result['number'] = order_detail.number
        result['univalent'] = order_detail.univalent
        result['returns_sn'] = order_return.returns_sn
        result['status'] = order_return.status
        result['add_time'] = order_return.add_time
        data.append(result)
    response = APIResponse(success=True, data=data, msg='全部退货单')
    return response


def supplier_confirm_order(order_sn):
    order_returns = OrderReturns.objects.filter(order_sn=order_sn, status=1).order_by('-add_time')
    if order_returns:
        order_return = order_returns[0]
        # 执行退款逻辑
        headers = {'content-type': 'application/json',
                   'user-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
        parameters = json.dumps({'order_sn': order_return.order_sn})
        try:
            response = requests.post(ORDER_API_HOST + '/api/refund', data=parameters, headers=headers)
            response_dict = json.loads(response.text)
        except Exception as e:
            logger.info('ID生成器连接失败!!!')
            response = APIResponse(success=False, data={}, msg='ID生成器连接失败!!!')
            return response
        if response_dict['rescode'] != '10000':
            response = APIResponse(success=False, data={}, msg='ID生成器出错!!!')
            return response
        refund_sn = response_dict['data']['tk_order_id']

        order_return.status = 2
        order_return.save()
        order_detail = OrderDetail.objects.get(son_order_sn=order_return.order_sn)
        order_detail.status = 10
        order_detail.save()
        supplier_id = order_detail.supplier_id
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=order_return.order_sn, status=14,
                                            operator=supplier_id,
                                            execution_detail='供应商[%s]执行订单[%s]确认收货操作' %
                                                             (order_detail.supplier_id, order_sn),
                                            progress='已收货', time_consuming=time_consuming)

        OrderRefund.objects.create(order_sn=order_detail.son_order_sn, refund_sn=refund_sn,
                                   amount=order_detail.subtotal_money, status=1)
        OrderOperationRecord.objects.create(order_sn=order_return.order_sn, status=11,
                                            operator=0,
                                            execution_detail='系统自动生成退款单',
                                            progress='退款中', time_consuming=time_consuming)
        # 通知财务系统开始退款逻辑
        pass
        response = APIResponse(success=True, data={}, msg='供应商确认收货成功,生成退款单成功')
    else:
        response = APIResponse(success=False, data={}, msg='确认收货操作传入的参数有误')
    return response


def user_confirm_order(instance, guest_id):
    if not isinstance(instance, OrderDetail):
        response = APIResponse(success=False, data={})
        return response
    if instance.status != 5:
        response = APIResponse(success=False, data={}, msg='当前状态不允许执行确认收货操作')
        return response
    now = datetime.now()
    order_operation = OrderOperationRecord.objects.filter(order_sn=instance.son_order_sn).order_by('-add_time')
    time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
    OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=7, operator=guest_id,
                                        execution_detail='用户[%s]对订单[%s]执行确认收货操作' % (guest_id, instance.son_order_sn),
                                        progress='确认收货', time_consuming=time_consuming)
    instance.status = 6
    instance.save()
    response = APIResponse(success=True, data={}, msg='确认收货操作成功')
    return response


def filter_base(order_details, order_sn='', goods_name='', brand='', start_time='', end_time=''):
    if order_sn:
        if order_sn.endswith('000000'):
            order = Order.objects.get(order_sn=order_sn)
            order_details = order_details.filter(order=order.id)
        else:
            order_details = order_details.filter(son_order_sn=order_sn)
    if goods_name:
        order_details = order_details.filter(goods_name=goods_name)

    if brand:
        order_details = order_details.filter(brand=brand)
    return order_details
