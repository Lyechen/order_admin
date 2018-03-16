import json
import requests

from rest_framework import mixins
from rest_framework import viewsets
from django.db.models import Q
from datetime import datetime, timedelta

from .serializers import OrderSerializer, OrderDetailSerializer, OrderCancelSerializer, OrderPaymentSerializer
from .serializers import UserOrderSerializer, AdminOrderCancelSerializer
from .serializers import SupplierOrderAdminSerializer, OrderLogisticsSerializer, ReceiptSerializer
from .serializers import OpenReceiptSerializer, AbnormalOrderSerializer, ChiefUpdateOrderSerializer
from .serializers import SupplierUpdateOrderSerializer, SuperUserUpdateSerializer, ChiefCancelOrderSerializer
from .serializers import ReturnsSerializer, ReturnOrderSerializer
from .models import Order, Receipt, OrderDetail, OrderLogistics, OrderOperationRecord, OrderPayment, OrderCancel
from .models import OpenReceipt, AbnormalOrder, SuperUserOperation, ReturnsDeal, OrderReturns, OrderRefund
from order_admin.settings import ORDER_API_HOST
from utils.log import logger
from utils.string_extension import safe_int, safe_float
from utils.http import APIResponse, CONTENT_RANGE, CONTENT_TOTAL
from order_admin.settings import CDN_HOST
from .functions import generation_order, get_mother_order_detail, get_son_order_detail, get_user_order_list
from .functions import payment_order, get_chief_order, deal_supplier_operation, supplier_confirm_order, filter_base
from .functions import superuser_get_order_detail, returns_order, deal_returns_order, user_confirm_order
from .functions import refund_detail, returns_detail, online_generation_order
from auth.authentication import UserAuthentication, AdminUserAuthentication, SupplierAuthentication

# Create your views here.

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
    10: '退款',
    11: '退货中',
    12: '作废',
    13: '无货',
    14: '退款完成',
    15: '退货完成',
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
    '退款完成': 14,
    '退货完成': 15,
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


class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,
                   mixins.DestroyModelMixin, viewsets.GenericViewSet):
    # serializer_class = OrderSerializer
    queryset = Order.objects.all()
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        # serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # self.perform_create(serializer)
        # 生成订单逻辑
        data = request.data.get('data', '')
        if not data:
            response = APIResponse(success=False, data={}, msg='参数异常')
            return response
        is_product = request.query_params.get('is_product', 0)
        if is_product:
            response = online_generation_order(data)
            return response
        response = generation_order(data)
        return response
        # data = re.sub('\'', '\"', request.data['data'])
        # now = datetime.now()
        # date = now.date()
        # delta = timedelta(days=15)
        # due_time = date + delta
        # try:
        #     data = json.loads(data)
        #     # 发票信息
        #     if data[0]['receipt_type'] == 3:
        #         receipt = Receipt.objects.create(receipt_type=data[0]['receipt_type'])
        #     else:
        #         receipt = Receipt.objects.create(
        #             title=data[0]['title'],
        #             account=data[0]['account'],
        #             tax_number=data[0]['tax_number'],
        #             telephone=data[0]['telephone'],
        #             bank=data[0]['bank'],
        #             company_address=data[0]['company_address'],
        #             receipt_type=data[0]['receipt_type'],
        #         )
        #     # 收货人
        #     receiver = data[0]['receiver']
        #     # 电话
        #     mobile = data[0]['mobile']
        #     # 收货地址
        #     address = data[0]['address']
        #     # 备注
        #     remarks = data[0]['remarks']
        #     # 买家ID
        #     guest_id = data[0]['guest_id']
        #     # 这里后续需要加上获取佣金比例的逻辑 暂时先用 0.0 替代
        #     ratio = 0.0
        #     order_status = 1
        #     headers = {'content-type': 'application/json',
        #                'user-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
        #     parameters = json.dumps({})
        #     try:
        #         response = requests.post(ORDER_API_HOST + '/api/order', data=parameters, headers=headers)
        #         response_dict = json.loads(response.text)
        #     except Exception as e:
        #         logger.info('ID生成器连接失败!!!')
        #         response = APIResponse(success=False, data={}, msg='ID生成器连接失败!!!')
        #         return response
        #     # 母订单号
        #     mother_order_sn = response_dict['data']['order_sn']
        #     # 创建母订单信息, 母订单类型订单不存在母订单
        #     mother_order = Order.objects.create(receipt=receipt.id, remarks=remarks, receiver=receiver, mobile=mobile,
        #                                         guest_id=guest_id, order_sn=mother_order_sn, address=address)
        #     # 增加母订单状态信息
        #     OrderOperationRecord.objects.create(order_sn=mother_order.order_sn, status=1, operator=guest_id,
        #                                         execution_detail='提交订单', progress='未支付')
        #     # 增加初始订单支付信息
        #     OrderPayment.objects.create(order_sn=mother_order_sn, pay_status=1)
        #     total_money = 0.0
        #     for _data in data:
        #         parameters = json.dumps({'order_id': mother_order_sn})
        #         response = requests.post(ORDER_API_HOST + '/api/order', data=parameters, headers=headers)
        #         order_sn = json.loads(response.text)['data']['order_sn']
        #         price_discount = float(_data.get('price_discount', 0.0))
        #         subtotal_money = float(_data['univalent']) * float(_data['number']) * (1.0 - price_discount)
        #         total_money += subtotal_money
        #         _order = OrderDetail.objects.create(
        #             order=mother_order.id,
        #             son_order_sn=order_sn,
        #             supplier_id=_data['supplier_id'],
        #             goods_id=_data['goods_id'],
        #             model=_data['model'],
        #             brand=_data['brand'],
        #             number=int(_data['number']),
        #             univalent=float(_data['univalent']),
        #             subtotal_money=subtotal_money,
        #             commission=subtotal_money * ratio,
        #             price_discount=price_discount,
        #             status=order_status,
        #             max_delivery_time=_data['max_delivery_time'],
        #             due_time=due_time
        #         )
        #         # 增加子订单状态信息
        #         OrderOperationRecord.objects.create(order_sn=_order.son_order_sn, status=1, operator=guest_id,
        #                                             execution_detail='提交订单', progress='未支付')
        #         OrderPayment.objects.create(order_sn=_order.son_order_sn, pay_status=1)
        #     mother_order.total_money = total_money
        #     mother_order.save()
        # except json.JSONDecodeError as e:
        #     logger.info("{msg: 请求参数异常}")
        #     response = APIResponse(success=False, data={}, msg='请求参数异常')
        #     return response
        # result = {
        #     'id': mother_order.id,
        #     'mother_order_sn': mother_order_sn,
        #     'add_time': mother_order.add_time,
        #     'address': mother_order.address,
        #     'receipt_title': data[0]['title'],
        #     'receipt_type': RECEIPT_TYPE[receipt.receipt_type],
        #     'status': ORDER_STATUS[order_status]
        # }
        # response = APIResponse(success=True, data=result, msg='创建订单信息成功')
        # return response

    def retrieve(self, request, *args, **kwargs):
        # 默认为子订单, 2为母订单
        order_type = safe_int(request.query_params.get('order_type', 1))
        guest_id = self.request.query_params.get('guest_id', 0)
        try:
            instance = self.get_object()
        except Exception as e:
            logger.info('传入参数异常或订单不存在')
            response = APIResponse(success=False, data={}, msg='传入参数异常或订单不存在')
            return response
        serializer = self.get_serializer(instance)
        # result = serializer.data
        if order_type == 1:
            response = get_son_order_detail(instance, guest_id)
            return response
        response = get_mother_order_detail(instance, serializer)
        return response
        # if order_type == 1:
        #     data = []
        #     _instance = instance
        #     instance = Order.objects.filter(pk=instance.order)
        #     if instance[0].guest_id != int(guest_id):
        #         response = APIResponse(success=False, data={})
        #         return response
        #     result = {}
        #     receipt = Receipt.objects.get(pk=instance[0].receipt)
        #     result['receipt_title'] = receipt.title
        #     result['account'] = receipt.account
        #     result['tax_number'] = receipt.tax_number
        #     result['telephone'] = receipt.telephone
        #     result['bank'] = receipt.bank
        #     result['company_address'] = receipt.company_address
        #     result['receipt_type'] = receipt.receipt_type
        #     result['guest_id'] = instance[0].guest_id
        #     result['total_money'] = instance[0].total_money
        #     result['add_time'] = instance[0].add_time.date()
        #     now = datetime.now()
        #     delta = timedelta(days=7)
        #     count_down = instance[0].add_time + delta - now
        #     result['order_sn'] = instance[0].order_sn
        #     result['count_down'] = count_down
        #     sub_order = []
        #     __dict = {}
        #     abnormal_delay_order = AbnormalOrder.objects.filter(order_sn=_instance.son_order_sn,
        #                                                         abnormal_type=2,
        #                                                         is_deal=2)
        #     abnormal_no_order = AbnormalOrder.objects.filter(order_sn=_instance.son_order_sn,
        #                                                      abnormal_type=1,
        #                                                      is_deal=2)
        #     if not abnormal_delay_order and _instance.status == 8:
        #         _status = '待接单'
        #     elif not abnormal_no_order and _instance.status == 13:
        #         _status = '待接单'
        #     else:
        #         _status = ORDER_STATUS[_instance.status]
        #     pay_status = OrderPayment.objects.filter(order_sn=_instance.son_order_sn).order_by('-add_time')[
        #         0].pay_status
        #     __dict['son_order_sn'] = _instance.son_order_sn
        #     __dict['number'] = _instance.number
        #     __dict['univalent'] = _instance.univalent
        #     __dict['max_delivery_time'] = _instance.max_delivery_time
        #     __dict['order_status'] = _status
        #     __dict['pay_status'] = PAY_STATUS[pay_status]
        #     sub_order.append(__dict)
        #     result['sub_order'] = sub_order
        #     data.append(result)
        #     response = APIResponse(success=True, data=data)
        #     return response
        # if instance.guest_id != int(guest_id):
        #     response = APIResponse(success=False, data={})
        #     return response
        # receipt = Receipt.objects.get(pk=serializer.data['receipt'])
        # result['receipt_title'] = receipt.title
        # result['account'] = receipt.account
        # result['tax_number'] = receipt.tax_number
        # result['telephone'] = receipt.telephone
        # result['bank'] = receipt.bank
        # result['company_address'] = receipt.company_address
        # result['receipt_type'] = receipt.receipt_type
        # order_detail = OrderDetail.objects.filter(order=int(instance.id))
        # sub_order = []
        # for _order in order_detail:
        #     # _sub_order = {}
        #     # _sub_order['id'] = _order.id
        #     # _sub_order['order_sn'] = _order.son_order_sn
        #     # _sub_order['supplier_id'] = _order.supplier_id
        #     # _sub_order['goods_id'] = _order.goods_id
        #     # _sub_order['model'] = _order.model
        #     # _sub_order['brand'] = _order.brand
        #     # _sub_order['number'] = _order.number
        #     # _sub_order['univalent'] = _order.univalent
        #     # _sub_order['price_discount'] = _order.price_discount
        #     # _sub_order['delivery_time'] = _order.delivery_time
        #     # _sub_order['add_time'] = _order.add_time
        #     # sub_order.append(_sub_order)
        #     # 优化方法
        #     sub_order.append(model_to_dict(_order))
        # result['sub_order'] = sub_order
        # response = APIResponse(data=result, success=True)
        # return response

    def list(self, request, *args, **kwargs):
        # data = []
        offset = safe_int(request.query_params.get('offset', 0))
        limit = safe_int(request.query_params.get('limit', 15))
        # page_num = request.query_params.get('page_num', 1)
        # page_size = request.query_params.get('page_size', 10)
        guest_id = self.request.query_params.get('guest_id', 0)
        # 0: 全部订单  1: 待付款  2: 待收货 3: 售后
        is_type = int(self.request.query_params.get('is_type', 0))
        start_time = self.request.query_params.get('start_time', '')
        end_time = self.request.query_params.get('end_time', '')
        receiver = self.request.query_params.get('receiver', '')
        order_info = self.request.query_params.get('order_info', '')
        if is_type == 1:
            orders = Order.objects.filter(guest_id=guest_id,
                                          id__in=[obj.order for obj in OrderDetail.objects.filter(status=1)])
        elif is_type == 2:
            orders = Order.objects.filter(guest_id=guest_id,
                                          id__in=[obj.order for obj in
                                                  OrderDetail.objects.filter(status__in=[5])])
        elif is_type == 3:
            orders = Order.objects.filter(guest_id=guest_id, id__in=[obj.order for obj in
                                                                     OrderDetail.objects.filter(status=11)])
        else:
            orders = Order.objects.filter(guest_id=guest_id)
        # 分页逻辑
        # if int(page_num) < 0 or (int(page_num) - 1) * int(page_size) >= len(orders):
        #     response = APIResponse(data={}, success=False)
        #     return response
        # if int(page_num) * int(page_size) > len(orders):
        #     start_num = (int(page_num) - 1) * int(page_size)
        #     orders = orders[start_num:]
        # else:
        #     start_num = (int(page_num) - 1) * int(page_size)
        #     end_num = int(page_num) * int(page_size)
        #     orders = orders[start_num:end_num]

        if start_time:
            start_time += ' 23:59:59'
            orders = orders.filter(add_time__gte=start_time)
        if end_time:
            end_time += ' 23:59:59'
            orders = orders.filter(add_time__lte=end_time)
        if receiver:
            orders = orders.filter(receiver=receiver)
        if order_info:
            order_detail = OrderDetail.objects.filter(Q(son_order_sn=order_info) |
                                                      Q(order=Order.objects.filter(order_sn=order_info)[0].id))
            orders = Order.objects.filter(pk=order_detail.order)
        total = orders.count()
        count = len(OrderDetail.objects.filter(order__in=[obj.id for obj in orders]))
        orders = orders[offset:offset + limit]

        data = get_user_order_list(orders, count)

        # for order in orders:
        #     _dict = {}
        #     receipt = Receipt.objects.get(pk=order.receipt)
        #     _dict['mother_order_id'] = order.id
        #     _dict['receipt_title'] = receipt.title
        #     _dict['account'] = receipt.account
        #     _dict['tax_number'] = receipt.tax_number
        #     _dict['telephone'] = receipt.telephone
        #     _dict['bank'] = receipt.bank
        #     _dict['company_address'] = receipt.company_address
        #     _dict['receipt_type'] = receipt.receipt_type
        #     _dict['guest_id'] = order.guest_id
        #     _dict['order_sn'] = order.order_sn
        #     _dict['receiver'] = order.receiver
        #     _dict['mobile'] = order.mobile
        #     _dict['total_money'] = order.total_money
        #     _dict['remarks'] = order.remarks
        #     _dict['address'] = order.address
        #     order_details = OrderDetail.objects.filter(order=order.id,
        #                                                status__in=[1, 3, 4, 5, 6, 8, 10, 11, 12, 13, 14, 15])
        #     _dict['type_count'] = count
        #     order_details = order_details[:1]
        #     result = []
        #     for order_detail in order_details:
        #         __dict = {}
        #         __dict['son_order_id'] = order_detail.id
        #         __dict['son_order_sn'] = order_detail.son_order_sn
        #         __dict['supplier_id'] = order_detail.supplier_id
        #         __dict['goods_id'] = order_detail.goods_id
        #         __dict['model'] = order_detail.model
        #         __dict['brand'] = order_detail.brand
        #         __dict['number'] = order_detail.number
        #         __dict['univalent'] = order_detail.univalent
        #         __dict['subtotal_money'] = order_detail.subtotal_money
        #         __dict['price_discount'] = order_detail.price_discount
        #         __dict['delivery_time'] = order_detail.delivery_time
        #         __dict['status'] = order_detail.status
        #         __dict['max_delivery_time'] = order_detail.max_delivery_time
        #         result.append(__dict)
        #     _dict['sub_order'] = result
        #     data.append(_dict)
        response = APIResponse(data=data, success=True, msg='%s号用户订单列表' % guest_id)
        response[CONTENT_RANGE] = '{0}-{1}'.format(offset, len(orders) - 1)
        response[CONTENT_TOTAL] = total
        return response

    def update(self, request, *args, **kwargs):
        guest_id = self.request.query_params.get('guest_id', 0)
        status = safe_int(self.request.data.get('status', 0))
        remarks = self.request.data.get('remarks', '')
        if not guest_id:
            response = APIResponse(data={}, success=False, msg='调用参数有误,guest_id不能为空')
            return response
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        if status == 3:
            """确认收货逻辑"""
            try:
                instance = self.get_object()
            except Exception as e:
                response = APIResponse(success=False, data={}, msg='ID有误')
                return response

            response = user_confirm_order(instance, guest_id)
            return response
        elif status:
            if not remarks:
                response = APIResponse(success=False, data={}, msg='remarks:不能为空')
                return response
            instance = self.get_object()
            response = returns_order(instance, status, guest_id, remarks)
            return response
        response = payment_order(serializer, guest_id)
        return response
        # trade_no = serializer.data['trade_no']
        # pay_type = serializer.data['pay_type']
        # order_sn = serializer.data['order_sn']
        # order = Order.objects.get(order_sn=order_sn)
        # orders = OrderDetail.objects.filter(order=order.id, status=1)
        # OrderPayment.objects.create(order_sn=order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
        # OrderOperationRecord.objects.create(order_sn=order_sn, status=2, operator=guest_id,
        #                                     execution_detail='用户[%s]对订单[%s]执行支付操作,使用[%s]方式支付' % (
        #                                         guest_id, order_sn, PAY_TYPE[pay_type]), progress='已支付')
        # for order in orders:
        #     # OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=2, operator=guest_id,
        #     #                                     execution_detail=PAY_TYPE[pay_type], progress='已支付')
        #     # # 创建一条系统记录
        #     # OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=4, operator=0,
        #     #                                     execution_detail='接单提醒', progress='已支付')
        #     OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=2, operator=guest_id,
        #                                         execution_detail='用户[%s]对订单[%s]执行支付操作,使用[%s]方式支付' % (
        #                                             guest_id, order.son_order_sn, PAY_TYPE[pay_type]), progress='已支付')
        #     OrderPayment.objects.create(order_sn=order.son_order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
        #     order.status = 3
        #     order.save()
        # response = APIResponse(data={}, success=True, msg='订单支付状态修改成功')
        # return response

    def destroy(self, request, *args, **kwargs):
        pass

    def get_object(self):
        order_type = self.request.query_params.get('order_type', 1)
        pk = self.kwargs.get('pk')
        if int(order_type) == 1:
            # 1: 子订单
            return OrderDetail.objects.get(pk=pk)
        else:
            return Order.objects.get(pk=pk)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            order_type = self.request.query_params.get('order_type', 1)
            if safe_int(order_type) == 1:
                return UserOrderSerializer
            else:
                return OrderDetailSerializer
        elif self.action == 'create':
            return OrderSerializer
        elif self.action == 'update':
            is_type = safe_int(self.request.query_params.get('is_type', 1))
            if is_type == 2:
                return ReturnsSerializer
            return OrderPaymentSerializer
        return OrderDetailSerializer


class OrderCancelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """取消订单"""
    serializer_class = OrderCancelSerializer
    queryset = OrderOperationRecord.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        order_sn = serializer.validated_data['order_sn']
        guest_id = serializer.validated_data['guest_id']
        order_status = 2
        now = datetime.now()
        # order = Order.objects.get(order_sn=order_sn)
        if order_sn.endswith('000000'):
            """取消母订单,需要将所有子订单都取消"""
            logger.info('母订单[%s]被取消.' % order_sn)
            OrderCancel.objects.create(order_sn=order_sn, responsible_party=1, cancel_desc='')
            order = Order.objects.get(order_sn=order_sn)
            sub_order = OrderDetail.objects.filter(order=order.id, status=1)
            time_consuming = 0
            for _order in sub_order:
                _order.status = order_status
                logger.info('子订单[%s]被取消,隶属母订单为[%s].' % (_order.son_order_sn, order_sn))
                time_consuming = float(now.timestamp() - sub_order.order_by('-add_time')[0].add_time.timestamp())
                OrderOperationRecord.objects.create(order_sn=_order.son_order_sn, status=3, operator=guest_id,
                                                    execution_detail='已取消', progress='未支付',
                                                    time_consuming=time_consuming)
                OrderCancel.objects.create(order_sn=_order.son_order_sn, responsible_party=1, cancel_desc='')
                _order.save()
            OrderOperationRecord.objects.create(order_sn=order_sn, status=3, operator=guest_id,
                                                execution_detail='已取消', progress='未支付',
                                                time_consuming=time_consuming)
            # order.save()
        else:
            """取消子订单"""
            order = OrderDetail.objects.get(son_order_sn=order_sn)
            OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=3, operator=guest_id,
                                                execution_detail='已取消', progress='未支付')
            OrderCancel.objects.create(order_sn=order.son_order_sn, responsible_party=1, cancel_desc='')
            order.status = order_status
            logger.info('子订单[%s]被取消.' % order_sn)
            order.save()
            # 取消子订单还需要修改母订单的总金额
            mother_order = Order.objects.get(pk=order.order)
            mother_order.total_money -= order.univalent * order.number * (1.0 - order.price_discount)
            mother_order.save()
        response = APIResponse(data={}, success=True, msg='取消订单成功')
        return response


class OrderPaymentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderPaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        trade_no = serializer.data['trade_no']
        pay_type = serializer.data['pay_type']
        order_sn = serializer.data['order_sn']
        guest_id = Order.objects.get(order_sn=order_sn).guest_id
        order = Order.objects.get(order_sn=order_sn)
        orders = OrderDetail.objects.filter(order=order.id, status=1)
        OrderPayment.objects.create(order_sn=order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
        OrderOperationRecord.objects.create(order_sn=order_sn, status=2, operator=guest_id,
                                            execution_detail='已支付', progress='已支付')
        for order in orders:
            order.status = 3
            OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=2, operator=guest_id,
                                                execution_detail=PAY_TYPE[pay_type], progress='已支付')
            # 创建一条系统记录
            OrderOperationRecord.objects.create(order_sn=order.son_order_sn, status=4, operator=0,
                                                execution_detail='接单提醒', progress='已支付')
            OrderPayment.objects.create(order_sn=order.son_order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
            order.save()
        response = APIResponse(data={}, success=True, msg='订单支付状态修改成功')
        return response


class ChiefOrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = OrderDetail.objects.all()

    # serializer_class = UserOrderSerializer

    # 使用django-filter
    # from rest_framework import filters
    # import django_filters
    # filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    # filter_fields = ('son_order_sn', 'supplier_id')
    # filter_class = UserOrderFilter

    def list(self, request, *args, **kwargs):
        is_abnormal = False
        offset = safe_int(request.query_params.get('offset', 0))
        limit = safe_int(request.query_params.get('limit', 15))
        # page_num = request.query_params.get('page_num', 1)
        # page_size = request.query_params.get('page_size', 10)
        guest_order_sn = request.query_params.get('guest_order_sn', '')
        pay_status = request.query_params.get('pay_status', '')
        order_status = request.query_params.get('order_status', '')
        supplier_name = request.query_params.get('supplier_name', '')
        guest_company_name = request.query_params.get('guest_company_name', '')
        start_time = request.query_params.get('start_time', '')
        end_time = request.query_params.get('end_time', '')
        # 0: 客户订单列表  1: 异常订单列表
        is_type = safe_int(request.query_params.get('is_type', 0))
        # 0: 全部  1: 无货  2: 延期
        abnormal_type = safe_int(request.query_params.get('abnormal_type', 0))
        if guest_order_sn and guest_order_sn.endswith('000000'):
            orders = Order.objects.filter(order_sn=guest_order_sn)
            order_details = OrderDetail.objects.filter(order=orders[0].id)
        elif guest_order_sn:
            order_details = OrderDetail.objects.filter(son_order_sn=guest_order_sn)
            # orders = Order.objects.filter(pk=order_details[0].order)
        else:
            # orders = Order.objects.all()
            order_details = OrderDetail.objects.all()
        # if (page_num - 1) * 10 > len(order_details):
        #     response = APIResponse(data={}, success=False, msg='传入页数不对')
        #     return response
        if is_type == 1:
            is_abnormal = True
            order_details = order_details.filter(status__in=[8, 13])
            if abnormal_type == 1:
                order_details = order_details.filter(status=13)
            elif abnormal_type == 2:
                order_details = order_details.filter(status=8)
        else:
            order_details = order_details.exclude(status__in=[8, 13])
        if order_status and int(order_status):
            order_details = order_details.filter(status=order_status)
        if start_time:
            order_details = order_details.filter(add_time__gte=start_time)
        if end_time:
            end_time += ' 23:59:59'
            order_details = order_details.filter(add_time__lte=end_time)
        if supplier_name:
            order_details = order_details.filter(supplier_name=supplier_name)
        if guest_company_name:
            # _order_details = []
            # for order_detail in order_details:
            #     _order = Order.objects.get(pk=order_detail.order)
            #     if _order.guest_id == guest_id:
            #         _order_details.append(_order)
            # order_details = _order_details
            order_details = order_details.filter(guest_company_name__icontains=guest_company_name)
        if pay_status:
            _order_details = []
            for order_detail in order_details:
                _order = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn, pay_status__gte=pay_status)
                if len(_order) == 1:
                    _order_details.append(order_detail)
            order_details = _order_details
        # order_details = OrderDetail.objects.all()
        total = len(order_details)
        order_details = order_details[offset:offset + limit]
        result = get_chief_order(order_details, is_abnormal=is_abnormal)
        # result = []
        # # for order in orders:
        # for _order in order_details:
        #     __dict = {}
        #     order = Order.objects.get(pk=_order.order)
        #     __dict['id'] = _order.id
        #     __dict['guest_name'] = order.guest_id
        #     __dict['order_sn'] = order.order_sn
        #     __dict['receiver'] = order.receiver
        #     __dict['mobile'] = order.mobile
        #     __dict['address'] = order.address
        #     __dict['remarks'] = order.remarks
        #     __dict['total_money'] = order.total_money
        #     payment = OrderPayment.objects.filter(order_sn=_order.son_order_sn).order_by('-add_time')
        #     __dict['son_order_sn'] = _order.son_order_sn
        #     __dict['supplier_name'] = _order.supplier_id
        #     __dict['goods_id'] = _order.goods_id
        #     __dict['model'] = _order.model
        #     __dict['number'] = _order.number
        #     __dict['order_status'] = ORDER_STATUS[_order.status]
        #     __dict['univalent'] = _order.univalent
        #     __dict['price_discount'] = _order.price_discount
        #     __dict['max_delivery_time'] = _order.max_delivery_time
        #     __dict['pay_status'] = PAY_STATUS[1] if not payment else PAY_STATUS[payment[0].pay_status]
        #     __dict['commission'] = _order.commission
        #     __dict['add_time'] = _order.add_time.timestamp()
        #     result.append(__dict)
        response = APIResponse(data=result, success=True, msg='全部订单信息')
        response[CONTENT_RANGE] = '{0}-{1}'.format(offset, len(order_details) - 1)
        response[CONTENT_TOTAL] = total
        return response

    def retrieve(self, request, *args, **kwargs):
        _dict = {}
        try:
            instance = self.get_object()
        except Exception as e:
            response = APIResponse(data={}, success=False, msg='当前ID有误')
            return response
        order_details = instance
        order = Order.objects.get(pk=order_details.order)
        receipt = Receipt.objects.get(pk=order.receipt)
        payments = OrderPayment.objects.filter(order_sn=order_details.son_order_sn).order_by('-add_time')
        # _dict['pay_status'] = payments[0].pay_status
        # _dict['pay_type'] = payments[0].pay_type
        # _dict['id'] = order.id
        # _dict['guest_id'] = order.guest_id
        # _dict['order_sn'] = order.order_sn
        # _dict['receiver'] = order.receiver
        # _dict['mobile'] = order.mobile
        # _dict['address'] = order.address
        # _dict['remarks'] = order.remarks
        # _dict['total_money'] = order.total_money
        _dict['order_info'] = {
            'id': order.id,
            'order_sn': order.order_sn,
            'pay_status': payments[0].pay_status,
            'pay_type': payments[0].pay_type,
            'son_order_sn': order_details.son_order_sn,
            'order_status': order_details.status,
            'add_time': int(order_details.add_time.timestamp())
        }
        _dict['guest_info'] = {
            'guest_id': order.guest_id,
            'receiver': order.receiver,
            'mobile': order.mobile,
            'address': order.address,
            'remarks': order.remarks,
            'company_name': '',
        }
        _dict['receipt_info'] = {
            'title': receipt.title,
            'account': receipt.account,
            'tax_number': receipt.tax_number,
            'telephone': receipt.telephone,
            'bank': receipt.bank,
            'company_address': receipt.company_address,
            'receipt_type': receipt.receipt_type,
        }
        _dict['supplier_info'] = {
            'linkman': '',
            'mobile': '',
            'company_name': '',
            'address': '',
        }
        _dict['order_detail'] = {
            'number': order_details.number,
            'univalent': order_details.univalent,
            'model': order_details.model,
            'price_discount': order_details.price_discount,
            'goods_name': '',
            'goods_sn': '',
            'max_delivery_time': order_details.max_delivery_time,
            'subtotal_money': order_details.subtotal_money,
            'commission': order_details.commission,
        }
        logistics = OrderLogistics.objects.filter(order_sn=order_details.son_order_sn)
        _dict['delivery_info'] = {
            'goods_name': '',
            'goods_id': order_details.goods_id,
            'model': order_details.model,
            'brand': order_details.brand,
            'number': order_details.number,
            'logistics_company': '' if not logistics else logistics[0].logistics_number,
            'logistics_number': '' if not logistics else logistics[0].logistics_number,
            'date_of_delivery': '' if not logistics else logistics[0].add_time.timestamp(),
        }
        # 添加发票信息
        # _dict['title'] = receipt.title
        # _dict['account'] = receipt.account
        # _dict['tax_number'] = receipt.tax_number
        # _dict['telephone'] = receipt.telephone
        # _dict['bank'] = receipt.bank
        # _dict['company_address'] = receipt.company_address
        # _dict['receipt_type'] = receipt.receipt_type
        # _dict['son_order_sn'] = order_details.son_order_sn
        # _dict['supplier_id'] = order_details.supplier_id
        # _dict['goods_id'] = order_details.goods_id
        # _dict['model'] = order_details.model
        # _dict['number'] = order_details.number
        # _dict['univalent'] = order_details.univalent
        # _dict['price_discount'] = order_details.price_discount
        # _dict['max_delivery_time'] = order_details.max_delivery_time
        # _dict['order_status'] = order_details.status
        # _dict['due_time'] = order_details.due_time
        # _dict['due_desc'] = order_details.due_desc
        # _dict['add_time'] = int(order_details.add_time.timestamp())
        # _dict['commission'] = order_details.commission
        operation = []
        for _operation in OrderOperationRecord.objects.filter(order_sn=order_details.son_order_sn):
            __dict = {}
            record = _operation.status
            guest_id = _operation.operator if _operation.operator > 0 else '系统'
            __dict['record'] = record
            __dict['guest_id'] = guest_id
            __dict['execution_detail'] = _operation.execution_detail
            __dict['progress'] = _operation.progress
            __dict['is_abnormal'] = _operation.is_abnormal
            __dict['time_consuming'] = int(_operation.time_consuming)
            __dict['add_time'] = int(_operation.add_time.timestamp())
            operation.append(__dict)
        _dict['operation'] = operation
        response = APIResponse(data=_dict, success=True, msg='订单详细信息')
        return response

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Exception as e:
            response = APIResponse(data={}, msg='传入的id有误')
            return response
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        # if serializer.validated_data['is_type'] == 1:
        # 延期处理
        instance.due_time = serializer.validated_data['due_time']
        instance.due_desc = serializer.validated_data['due_desc']
        instance.save()
        OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=9, operator=0,
                                            execution_detail="运营后台更新延期时间", progress='已支付')
        # else:
        #     """取消订单"""
        #     responsible_party = serializer.validated_data['responsible_party']
        #     cancel_desc = serializer.validated_data['cancel_desc']
        #     OrderCancel.objects.create(order_sn=instance.son_order_sn, responsible_party=responsible_party,
        #                                cancel_desc=cancel_desc)
        #     instance.status = 2
        #     instance.save()
        #     OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=3, operator=0,
        #                                         execution_detail="运营后台取消订单", progress='已支付')
        response = APIResponse(data={}, success=True, msg='更新成功')
        return response

    def destroy(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        responsible_party = serializer.validated_data['responsible_party']
        cancel_desc = serializer.validated_data['cancel_desc']
        OrderCancel.objects.create(order_sn=instance.son_order_sn, responsible_party=responsible_party,
                                   cancel_desc=cancel_desc)
        instance.status = 2
        instance.save()
        OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=3, operator=0,
                                            execution_detail="运营后台取消订单", progress='已支付')
        response = APIResponse(data={}, success=True, msg='订单取消成功')
        return response

    def get_serializer_class(self):
        if self.action == 'update':
            return ChiefUpdateOrderSerializer
        elif self.action == 'destroy':
            return ChiefCancelOrderSerializer
        return UserOrderSerializer


class AdminOrderCancelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminOrderCancelSerializer
    queryset = OrderCancel.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        order_sn = serializer.data['order_sn']
        responsible_party = serializer.data['responsible_party']
        cancel_desc = serializer.data['cancel_desc']
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn)
        if order_detail:
            OrderCancel.objects.create(order_sn=order_sn, responsible_party=responsible_party, cancel_desc=cancel_desc)
            order_detail[0].status = 2
            order_detail[0].save()
            OrderOperationRecord.objects.create(order_sn=order_sn, status=3, operator=0,
                                                execution_detail="运营后台取消订单", progress='已支付')
        response = APIResponse(data={}, success=True, msg='取消订单成功')
        return response


class MyOrderViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderDetailSerializer
    queryset = Order.objects.all()

    def get_object(self):
        is_search = self.request.query_params.get('is_search', False)
        # is_type: 0 全部  1  代付款  2  待收货
        is_type = int(self.request.query_params.get('is_type', 0))
        if is_type == 1:
            orders = Order.objects.filter(guest_id=self.kwargs.get('pk', 0),
                                          id__in=[obj.order for obj in OrderDetail.objects.filter(status=1)])
        elif is_type == 2:
            orders = Order.objects.filter(guest_id=self.kwargs.get('pk', 0),
                                          id__in=[obj.order for obj in
                                                  OrderDetail.objects.filter(status__in=[6, 7, 10])])
        else:
            orders = Order.objects.filter(guest_id=self.kwargs.get('pk', 0))
        if int(is_search):
            start_time = self.request.query_params.get('start_time', '')
            end_time = self.request.query_params.get('end_time', '')
            receiver = self.request.query_params.get('receiver', '')
            order_info = self.request.query_params.get('order_info', '')
            if start_time:
                orders = orders.filter(add_time__gte=start_time)
            if end_time:
                end_time += ' 23:59:59'
                orders = orders.filter(add_time__lte=end_time)
            if receiver:
                orders = orders.filter(receiver=receiver)
            if order_info:
                order_detail = OrderDetail.objects.filter(Q(son_order_sn=order_info) |
                                                          Q(order=Order.objects.filter(order_sn=order_info)[0].id))
                orders = Order.objects.filter(pk=order_detail.order)
        return orders

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        is_detail = request.query_params.get('is_detail', 0)
        order_sn = request.query_params.get('order_sn', '')
        count = 0
        if int(is_detail):
            if not order_sn:
                response = APIResponse(success=False, data={}, msg='传入订单号不能为空')
                return response
            instance = instance.filter(order_sn=order_sn)
            order_details = OrderDetail.objects.filter(order=instance[0].id)
            count = len(order_details)
        else:
            order_details = []
            for order in instance:
                order_detail = OrderDetail.objects.filter(order=order.id)
                count = len(order_detail)
                order_detail = order_detail[0]
                order_details.append(order_detail)
        data = []
        for order in instance:
            result = {}
            result['guest_id'] = order.guest_id
            result['total_money'] = order.total_money
            result['add_time'] = order.add_time.date()
            now = datetime.now()
            delta = timedelta(days=7)
            count_down = order.add_time + delta - now
            result['order_sn'] = order.order_sn
            result['count_down'] = count_down
            sub_order = []
            for order_detail in filter(lambda x: x.order == order.id, order_details):
                __dict = {}
                abnormal_delay_order = AbnormalOrder.objects.filter(order_sn=order_detail.son_order_sn, abnormal_type=2,
                                                                    is_deal=2)
                abnormal_no_order = AbnormalOrder.objects.filter(order_sn=order_detail.son_order_sn, abnormal_type=1,
                                                                 is_deal=2)
                if not abnormal_delay_order and order_detail.status == 8:
                    _status = '待接单'
                elif not abnormal_no_order and order_detail.status == 13:
                    _status = '待接单'
                else:
                    _status = ORDER_STATUS[order_detail.status]
                pay_status = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn).order_by('-add_time')[
                    0].pay_status
                __dict['son_order_sn'] = order_detail.son_order_sn
                __dict['number'] = order_detail.number
                __dict['univalent'] = order_detail.univalent
                __dict['max_delivery_time'] = order_detail.max_delivery_time
                __dict['order_status'] = _status
                __dict['pay_status'] = PAY_STATUS[pay_status]
                sub_order.append(__dict)
            result['sub_order'] = sub_order
            result['count'] = count
            data.append(result)
        response = APIResponse(success=True, data=data, msg='我的订单')
        return response

    def update(self, request, *args, **kwargs):
        # instance = self.get_object()
        order_sn = self.request.data.get('order_sn', '')
        is_type = safe_int(self.request.query_params.get('is_type', 0))
        if is_type == 1:
            """退货确认收货"""
            response = supplier_confirm_order(order_sn)
            return response
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn, status=5)
        if not order_detail:
            response = APIResponse(success=False, data={}, msg='传入的订单号有误')
            return response
        order_detail[0].status = 6
        order_detail[0].save()
        guest_id = self.kwargs.get('pk', 0)
        now = datetime.now()
        time_consuming = float(now.timestamp() - order_detail[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=order_sn, status=14,
                                            operator=guest_id,
                                            execution_detail='客户[%s]执行订单[%s]确认收货操作' % (guest_id, order_sn),
                                            progress='已收货', time_consuming=time_consuming)
        response = APIResponse(success=True, data={}, msg='确认收货操作成功')
        return response


class SupplierOrderAdminViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    serializer_class = SupplierOrderAdminSerializer
    queryset = OrderDetail.objects.all()

    # def get_object(self):
    #     supplier_id = self.kwargs.get('pk', 0)
    #     operation_type = self.request.data.get('type', '')
    #     order_sn = self.request.data.get('order_sn', '')
    #     if order_sn and operation_type == 'jd':
    #         order_details = OrderDetail.objects.filter(supplier_id=supplier_id, son_order_sn=order_sn)
    #         return order_details
    #     else:
    #         order_details = OrderDetail.objects.filter(supplier_id=supplier_id, status__in=[3, 4, 5, 6, 8, 9, 13])
    #     orders = Order.objects.filter(id__in=[obj.order for obj in order_details])
    #     return orders

    def list(self, request, *args, **kwargs):
        offset = safe_int(request.query_params.get('offset', 0))
        limit = safe_int(request.query_params.get('limit', 15))
        supplier_id = request.query_params.get('supplier_id', 0)
        order_sn = request.query_params.get('order_sn', '')
        goods_name = request.query_params.get('goods_name', '')
        order_status = request.query_params.get('order_status', '')
        brand = request.query_params.get('brand', '')
        start_time = request.query_params.get('start_time', '')
        end_time = request.query_params.get('end_time', '')
        # 0: 客户订单  1: 退货订单 2: 退款单
        is_type = safe_int(request.query_params.get('is_type', 0))
        if is_type:
            returns_sn = request.query_params.get('returns_sn', '')
            returns_status = safe_int(request.query_params.get('returns_status', 0))
            order_details = OrderDetail.objects.filter(supplier_id=supplier_id, status__in=[10, 11, 14, 15])
            if is_type == 1:
                order_details = order_details.filter(status__in=[11, 15])
            elif is_type == 2:
                order_details = order_details.filter(status__in=[10, 14])
            if order_sn:
                order_details = order_details.filter(son_order_sn=order_sn)
            order_details = filter_base(order_details, order_sn=order_sn, goods_name=goods_name, brand=brand)
            # if brand:
            #     order_details = order_details.filter(brand=brand)
            response = deal_returns_order(order_details, returns_status, returns_sn, start_time, end_time,
                                          is_type=is_type)
            return response
        order_details = OrderDetail.objects.filter(supplier_id=supplier_id, status__in=[3, 4, 5, 6, 8, 13])
        order_details = filter_base(order_details, order_sn=order_sn, goods_name=goods_name, brand=brand)
        # if order_sn:
        #     if order_sn.endswith('000000'):
        #         order = Order.objects.get(order_sn=order_sn)
        #         order_details = order_details.filter(order=order.id)
        #     else:
        #         order_details = order_details.filter(son_order_sn=order_sn)
        # if goods_name:
        #     order_details = order_details.filter(goods_name=goods_name)
        if order_status:
            order_details = order_details.filter(status=order_status)
        # if brand:
        #     order_details = order_details.filter(brand=brand)
        if start_time:
            start_time += ' 23:59:59'
            order_details = order_details.filter(add_time__gte=start_time)
        if end_time:
            end_time += ' 23:59:59'
            order_details = order_details.filter(add_time__lte=end_time)
        total = len(order_details)
        order_details = order_details[offset:offset + limit]
        orders = Order.objects.filter(id__in=[obj.order for obj in order_details])
        data = []
        # 为了数据结构前端方便处理 只能多采用一层循环
        for order in orders:
            result = {}
            result['total_money'] = order.total_money
            result['add_time'] = int(order.add_time.timestamp())
            result['order_sn'] = order.order_sn
            sub_order = []
            for order_detail in filter(lambda obj: obj.order == order.id, order_details):
                _result = {}
                _result['id'] = order_detail.id
                _result['son_order_sn'] = order_detail.son_order_sn
                _result['guest_company_name'] = order_detail.guest_company_name
                _result['receiver'] = order.receiver
                _result['mobile'] = order.mobile
                _result['address'] = order.province + order.city + order.district + order.address
                _result['supplier_id'] = order_detail.supplier_id
                _result['number'] = order_detail.number
                _result['univalent'] = order_detail.univalent
                _result['max_delivery_time'] = order_detail.max_delivery_time
                _result['status'] = order_detail.status
                _result['subtotal_money'] = order_detail.subtotal_money
                # 商品单位
                _result['goods_unit'] = order_detail.goods_id
                _result['goods_id'] = order_detail.goods_id
                # 商品名称
                _result['goods_name'] = '西门子电机'
                _result['model'] = order_detail.model
                _result['brand'] = order_detail.brand
                # 包邮类型 0 无需物流 1 买家承担运费 2 卖家承担运费
                _result['logistics_type'] = 1
                _result['commission'] = order_detail.commission
                _result['original_delivery_time'] = int((order_detail.add_time + timedelta(
                    days=order_detail.max_delivery_time)).timestamp())
                _open_receipt = []
                for open_receipt in OpenReceipt.objects.filter(order_sn=order_detail.son_order_sn):
                    _receipt = {}
                    _receipt['receipt_sn'] = open_receipt.receipt_sn
                    _receipt['order_sn'] = open_receipt.order_sn
                    _receipt['images'] = CDN_HOST + open_receipt.images if open_receipt.images else ''
                    _receipt['remarks'] = open_receipt.remarks
                    _receipt['add_time'] = int(open_receipt.add_time.timestamp())
                    _open_receipt.append(_receipt)
                _result['open_receipt'] = _open_receipt
                sub_order.append(_result)
            result['sub_order'] = sub_order
            data.append(result)
        response = APIResponse(success=True, data=data, msg='供应商[%s]的全部订单' % supplier_id)
        response[CONTENT_RANGE] = '{0}-{1}'.format(offset, len(order_details) - 1)
        response[CONTENT_TOTAL] = total
        return response

    def retrieve(self, request, *args, **kwargs):
        data = {}
        is_type = safe_int(request.query_params.get('is_type', 0))
        instance = self.get_object()
        supplier_id = request.query_params.get('supplier_id', 0)
        if safe_int(supplier_id) != instance.supplier_id:
            response = APIResponse(success=False, data={}, msg='供应商ID错误')
            return response
        order_detail = instance
        if order_detail.status in [11, 15] and is_type != 1:
            response = APIResponse(success=False, data={}, msg='传入参数有误')
            return response
        elif order_detail.status in [10, 14] and is_type != 2:
            response = APIResponse(success=False, data={}, msg='传入参数有误')
            return response
        elif order_detail.status not in [10, 11, 14, 15] and is_type:
            response = APIResponse(success=False, data={}, msg='传入参数有误')
            return response
        instance = Order.objects.filter(id=instance.order)
        if not instance:
            response = APIResponse(success=False, data={})
            return response
        order = instance[0]
        receipt = Receipt.objects.get(pk=order.receipt)
        data['order_info'] = {
            'receiver': order.receiver,
            'mobile': order.mobile,
            'address': order.address,
            'remarks': order.remarks,
            'son_order_sn': order_detail.son_order_sn,
            'subtotal_money': order_detail.subtotal_money,
            'supplier_id': order_detail.supplier_id,
            'number': order_detail.number,
            'univalent': order_detail.univalent,
            'max_delivery_time': order_detail.max_delivery_time,
            'status': order_detail.status,
            'goods_id': order_detail.goods_id,
            'goods_unit': order_detail.goods_unit,
            'goods_name': '西门子马达',
            'model': order_detail.model,
            'brand': order_detail.brand,
            'commission': order_detail.commission,
            'original_delivery_time': int((order_detail.add_time + timedelta(
                days=order_detail.max_delivery_time)).timestamp()),
            'add_time': int(order.add_time.timestamp())
        }
        if is_type == 1:
            response = returns_detail(order_detail, data)
            return response
        elif is_type == 2:
            response = refund_detail(order_detail, data)
            return response
        data['receipt_info'] = {
            'receipt_id': receipt.id,
            'title': receipt.title,
            'account': receipt.account,
            'tax_number': receipt.tax_number,
            'telephone': receipt.telephone,
            'bank': receipt.bank,
            'company_address': receipt.company_address,
            'add_time': int(receipt.add_time.timestamp())
        }
        payment = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn, pay_status=2)
        if not payment:
            response = APIResponse(success=False, data={}, msg='请求有误')
            return response
        payment = payment[0]
        data['pay_info'] = {
            'pay_type': payment.pay_type,
            'pay_status': payment.pay_status,
            'add_time': int(payment.add_time.timestamp())
        }
        _open_receipt = []
        for open_receipt in OpenReceipt.objects.filter(order_sn=order_detail.son_order_sn):
            _receipt = {}
            _receipt['receipt_sn'] = open_receipt.receipt_sn
            _receipt['order_sn'] = open_receipt.order_sn
            _receipt['images'] = CDN_HOST + open_receipt.images
            _receipt['remarks'] = open_receipt.remarks
            _receipt['add_time'] = int(open_receipt.add_time.timestamp())
            _open_receipt.append(_receipt)
        data['open_receipt'] = _open_receipt

        logistics = OrderLogistics.objects.filter(order_sn=order_detail.son_order_sn)
        _logistics = []
        for _log in logistics:
            _ = {}
            _['receiver'] = _log.receiver
            _['mobile'] = _log.mobile
            _['address'] = _log.address
            _['logistics_type'] = _log.logistics_type
            _['logistics_company'] = _log.logistics_company
            _['date_of_delivery'] = _log.date_of_delivery
            _['logistics_number'] = _log.logistics_number
            _['add_time'] = int(_log.add_time.timestamp())
            _['sender'] = _log.sender
            _logistics.append(_)
        data['logistics'] = _logistics

        order_operations = OrderOperationRecord.objects.filter(order_sn=order_detail.son_order_sn)
        _operations = []
        for operation in order_operations:
            _ = {}
            _['status'] = operation.status
            _['operator'] = operation.operator
            _['execution_detail'] = operation.execution_detail
            _['progress'] = operation.progress
            _['time_consuming'] = operation.time_consuming
            _['add_time'] = int(operation.add_time.timestamp())
            _operations.append(_)
        data['operations'] = _operations

        # for order in instance:
        #     result = {}
        #     result['total_money'] = order.total_money
        #     result['add_time'] = int(order.add_time.timestamp())
            # now = datetime.now()
            # delta = timedelta(days=7)
            # count_down = order.add_time + delta - now
            # result['order_sn'] = order.order_sn
            # result['count_down'] = count_down
            # result['receiver'] = order.receiver
            # result['mobile'] = order.mobile
            # result['address'] = order.address
            # result['remarks'] = order.remarks
            # receipt = Receipt.objects.get(pk=order.receipt)
            # result['receipt_id'] = receipt.id
            # result['title'] = receipt.title
            # result['account'] = receipt.account
            # result['tax_number'] = receipt.tax_number
            # result['telephone'] = receipt.telephone
            # result['bank'] = receipt.bank
            # result['company_address'] = receipt.company_address
            # sub_order = []
            # for order_detail in _instance:
                # __dict = {}
                # __dict['son_order_sn'] = order_detail.son_order_sn
                # __dict['supplier_id'] = order_detail.supplier_id
                # __dict['number'] = order_detail.number
                # __dict['univalent'] = order_detail.univalent
                # __dict['max_delivery_time'] = order_detail.max_delivery_time
                # __dict['status'] = ORDER_STATUS[order_detail.status]
                # __dict['subtotal_money'] = order_detail.subtotal_money
                # __dict['goods_id'] = order_detail.goods_id
                # __dict['goods_name'] = '西门子马达'
                # __dict['model'] = order_detail.model
                # __dict['brand'] = order_detail.brand
                # __dict['commission'] = order_detail.commission
                # __dict['original_delivery_time'] = int((order_detail.add_time + timedelta(
                #     days=order_detail.max_delivery_time)).timestamp())
                # 开票
                # _open_receipt = []
                # for open_receipt in OpenReceipt.objects.filter(order_sn=order_detail.son_order_sn):
                #     _receipt = {}
                #     _receipt['receipt_sn'] = open_receipt.receipt_sn
                #     _receipt['order_sn'] = open_receipt.order_sn
                #     _receipt['images'] = CDN_HOST + open_receipt.images
                #     _receipt['remarks'] = open_receipt.remarks
                #     _receipt['add_time'] = int(open_receipt.add_time.timestamp())
                #     _open_receipt.append(_receipt)
                # __dict['open_receipt'] = _open_receipt
                # payment = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn, pay_status=2)
                # if not payment:
                #     response = APIResponse(success=False, data={}, msg='请求有误')
                #     return response
                # payment = payment[0]
                # __dict['pay_type'] = PAY_TYPE[payment.pay_type]
                # __dict['pay_status'] = PAY_STATUS[payment.pay_status]
                # 物流
                # logistics = OrderLogistics.objects.filter(order_sn=order_detail.son_order_sn)
                # _logistics = []
                # for _log in logistics:
                #     ___dict = {}
                #     ___dict['receiver'] = _log.receiver
                #     ___dict['mobile'] = _log.mobile
                #     ___dict['address'] = _log.address
                #     ___dict['logistics_type'] = _log.logistics_type
                #     ___dict['logistics_company'] = _log.logistics_company
                #     ___dict['date_of_delivery'] = _log.date_of_delivery
                #     ___dict['logistics_number'] = _log.logistics_number
                #     _logistics.append(___dict)
                # __dict['logistics'] = _logistics
                # 订单操作
            #     order_operations = OrderOperationRecord.objects.filter(order_sn=order_detail.son_order_sn)
            #     _operations = []
            #     for operation in order_operations:
            #         _ = {}
            #         _['status'] = operation.status
            #         _['operator'] = operation.operator
            #         _['execution_detail'] = operation.execution_detail
            #         _['progress'] = operation.progress
            #         _['time_consuming'] = operation.time_consuming
            #         _['add_time'] = int(operation.add_time.timestamp())
            #         _operations.append(_)
            #     __dict['operations'] = _operations
            #     sub_order.append(__dict)
            # result['sub_order'] = sub_order
            # data.append(result)
        response = APIResponse(success=True, data=data, msg='供应商收到的订单')
        return response

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        order_sn = instance.son_order_sn
        original_delivery_time = request.data.get('original_delivery_time', '')
        abnormal_type = safe_int(request.data.get('abnormal_type'))
        operator = instance.supplier_id
        expect_date_of_delivery = request.data.get('expect_date_of_delivery', '')
        remarks = request.data.get('remarks', '')
        if abnormal_type in [1, 2]:
            # 无货  延期
            response = deal_supplier_operation(abnormal_type, order_sn, original_delivery_time, expect_date_of_delivery,
                                               operator, serializer, remarks)
            return response
        # elif is_type == 3:
        #     response = deal_supplier_operation(1, order_sn, original_delivery_time, expect_date_of_delivery, operator,
        #                                        serializer)
        #     return response
        if safe_int(serializer.validated_data['status']) == 1:
            response = APIResponse(success=False, data={}, msg='无需操作')
            return response
        elif safe_int(serializer.validated_data['status']) == 3:
            response = supplier_confirm_order(order_sn)
            return response
        supplier_id = safe_int(self.request.query_params.get('supplier_id', 0))
        if not supplier_id:
            response = APIResponse(success=False, data={}, msg='供应商ID不能为空')
            return response
        order_detail = instance
        if order_detail.status == 4:
            response = APIResponse(success=False, data={}, msg='不能重复接单!')
            return response
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=instance.son_order_sn).order_by(
            '-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        if order_detail.status not in [3]:
            response = APIResponse(success=False, data={}, msg='当前操作有误,或订单已接单')
            return response
        order_detail.status = 4
        order_detail.save()
        OrderOperationRecord.objects.create(order_sn=instance.son_order_sn, status=5,
                                            operator=supplier_id,
                                            execution_detail='供应商[%s]执行订单[%s]接单操作' %
                                                             (supplier_id, instance.son_order_sn),
                                            progress='已接单', time_consuming=time_consuming)
        data = {
            'supplier_id': supplier_id,
            'status': ORDER_STATUS[instance.status]
        }
        response = APIResponse(success=True, data=data, msg='接单操作成功')
        return response

    def get_serializer_class(self):
        if self.action == 'update':
            # 1: 无货  2: 延期
            abnormal_type = safe_int(self.request.data.get('abnormal_type'))
            if abnormal_type in [1, 2]:
                return AbnormalOrderSerializer
            return SupplierUpdateOrderSerializer
        return SupplierOrderAdminSerializer


class OrderLogisticsViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderLogisticsSerializer
    queryset = OrderLogistics.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.info('创建物流信息发生错误')
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        is_type = safe_int(self.request.query_params.get('is_type', 0))
        if is_type == 1:
            order_sn = serializer.data['order_sn']
            # 获取退货单号逻辑
            headers = {'content-type': 'application/json',
                       'user-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
            parameters = json.dumps({'order_sn': order_sn})
            try:
                response = requests.post(ORDER_API_HOST + '/api/rejected', data=parameters, headers=headers)
                response_dict = json.loads(response.text)
            except Exception as e:
                logger.info('ID生成器连接失败!!!')
                response = APIResponse(success=False, data={}, msg='ID生成器连接失败!!!')
                return response
            logger.info(message='生成退货ID返回结果: %s' % response_dict)
            if response_dict['rescode'] != '10000':
                response = APIResponse(success=False, data={}, msg='ID生成器出错!!!')
                return response
            returns_sn = response_dict['data']['th_order_id']
            receiver = serializer.data['receiver']
            mobile = serializer.data['mobile']
            logistics_company = serializer.data['logistics_company']
            logistics_number = serializer.data['logistics_number']
            now = datetime.now()
            order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
            time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
            order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
            if order_detail.status != 11:
                response = APIResponse(success=False, data={}, msg='当前状态不允许退货')
                return response
            order = Order.objects.get(pk=order_detail.order)
            OrderReturns.objects.create(order_sn=order_sn, returns_sn=returns_sn, receiver=receiver, mobile=mobile,
                                        logistics_company=logistics_company, logistics_number=logistics_number,
                                        status=1)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=6,
                                                operator=order.guest_id,
                                                execution_detail='客户[%s]对订单[%s]填写物流信息' %
                                                                 (order.guest_id, order_sn),
                                                progress='已发货', time_consuming=time_consuming)
            response = APIResponse(success=True, data=serializer.data, msg='创建物流信息成功')
            return response
        order_sn = serializer.validated_data['order_sn']
        order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
        if order_detail.status == 11:
            response = APIResponse(data={}, success=False, msg='当前订单状态为退货中,只允许客户发货')
            return response
        self.perform_create(serializer)
        order_detail.status = 5
        order_detail.save()
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        OrderOperationRecord.objects.create(order_sn=order_sn, status=6,
                                            operator=order_detail.supplier_id,
                                            execution_detail='供应商[%s]执行订单[%s]发货操作' %
                                                             (order_detail.supplier_id, order_sn),
                                            progress='已发货', time_consuming=time_consuming)
        response = APIResponse(success=True, data=serializer.validated_data, msg='创建物流信息成功')
        return response

    def get_serializer_class(self):
        is_type = safe_int(self.request.query_params.get('is_type', 0))
        if self.action == 'create':
            if is_type == 1:
                return ReturnOrderSerializer
            return OrderLogisticsSerializer


class ReceiptViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ReceiptSerializer
    queryset = Receipt.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        result = serializer.data
        result['images'] = CDN_HOST + result['images'] if result['images'] else ''
        response = APIResponse(success=True, data=result, msg='创建开票信息成功')
        return response

    def get_serializer_class(self):
        if self.action == 'create':
            return OpenReceiptSerializer
        return ReceiptSerializer


class AbnormalOrderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AbnormalOrderSerializer
    queryset = AbnormalOrder.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            non_field_errors = ''
            if hasattr(e, 'detail'):
                if e.detail.get('non_field_errors', ''):
                    non_field_errors = e.detail.get('non_field_errors')[0]
                else:
                    non_field_errors = e.detail
            response = APIResponse(data={}, success=False, msg=non_field_errors if non_field_errors else '请求出错')
            return response
        self.perform_create(serializer)
        order_sn = serializer.data['order_sn']
        original_delivery_time = serializer.data['original_delivery_time']
        abnormal_type = serializer.data['abnormal_type']
        expect_date_of_delivery = serializer.data['expect_date_of_delivery']
        # 无货
        if abnormal_type == 1:
            order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
            order_detail.status = 13
            order_detail.save()
            now = datetime.now()
            order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
            time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
            OrderOperationRecord.objects.create(order_sn=order_sn, status=8,
                                                operator=order_detail.supplier_id,
                                                execution_detail='供应商[%s]执行订单[%s]无货操作' %
                                                                 (order_detail.supplier_id, order_sn),
                                                progress='待接单,无货', time_consuming=time_consuming)
        else:
            order_detail = OrderDetail.objects.get(son_order_sn=order_sn)
            order_detail.status = 8
            order_detail.max_delivery_time = (expect_date_of_delivery - original_delivery_time).days
            order_detail.save()
            now = datetime.now()
            order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
            time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
            OrderOperationRecord.objects.create(order_sn=order_sn, status=10,
                                                operator=order_detail.supplier_id,
                                                execution_detail='供应商[%s]执行订单[%s]申请延期操作' %
                                                                 (order_detail.supplier_id, order_sn),
                                                progress='申请延期', time_consuming=time_consuming)
        response = APIResponse(success=True, data=serializer.data)
        return response


class SupperUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                        mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = OrderDetail.objects.all()

    # serializer_class = SuperUserUpdateSerializer

    # permission_classes =

    def list(self, request, *args, **kwargs):
        offset = safe_int(request.query_params.get('offset', 0))
        limit = safe_int(request.query_params.get('limit', 15))
        # 0: 全部订单  1: 待付款  2: 待收货
        order_type = safe_int(self.request.query_params.get('order_type', 0))
        start_time = self.request.query_params.get('start_time', '')
        end_time = self.request.query_params.get('end_time', '')
        receiver = self.request.query_params.get('receiver', '')
        guest_id = safe_int(self.request.query_params.get('guest_id', ''))
        orders = Order.objects.all()
        if guest_id:
            orders = orders.filter(guest_id=guest_id)
        if order_type == 1:
            orders = Order.objects.filter(id__in=[obj.order for obj in OrderDetail.objects.filter(status=1)])
        elif order_type == 2:
            orders = Order.objects.filter(id__in=[obj.order for obj in OrderDetail.objects.filter(status__in=[6, 10])])
        if start_time:
            start_time += ' 23:59:59'
            orders = orders.filter(add_time__gte=start_time)
        if end_time:
            end_time += ' 23:59:59'
            orders = orders.filter(add_time__lte=end_time)
        if receiver:
            orders = orders.filter(receiver=receiver)
        count = len(OrderDetail.objects.filter(order__in=[obj.id for obj in orders]))
        total = len(orders)
        orders = orders[offset:offset + limit]
        data = get_user_order_list(orders, count, is_all=True)
        # for order in orders:
        #     _dict = {}
        #     receipts = Receipt.objects.filter(pk=order.receipt)
        #     _dict['id'] = order.id
        #     for receipt in receipts:
        #         _dict['title'] = receipt.title
        #         _dict['account'] = receipt.account
        #         _dict['tax_number'] = receipt.tax_number
        #         _dict['telephone'] = receipt.telephone
        #         _dict['bank'] = receipt.bank
        #         _dict['company_address'] = receipt.company_address
        #         _dict['receipt_type'] = receipt.receipt_type
        #         _dict['add_time'] = receipt.add_time
        #     _dict['guest_id'] = order.guest_id
        #     _dict['order_sn'] = order.order_sn
        #     _dict['receiver'] = order.receiver
        #     _dict['mobile'] = order.mobile
        #     _dict['address'] = order.address
        #     _dict['remarks'] = order.remarks
        #     _dict['total_money'] = order.total_money
        #     order_details = OrderDetail.objects.filter(order=order.id)
        #     result = []
        #     for order_detail in order_details:
        #         __dict = {}
        #         __dict['son_order_sn'] = order_detail.son_order_sn
        #         __dict['supplier_id'] = order_detail.supplier_id
        #         __dict['goods_id'] = order_detail.goods_id
        #         __dict['model'] = order_detail.model
        #         __dict['brand'] = order_detail.brand
        #         __dict['number'] = order_detail.number
        #         __dict['univalent'] = order_detail.univalent
        #         __dict['subtotal_money'] = order_detail.subtotal_money
        #         __dict['price_discount'] = order_detail.price_discount
        #         __dict['delivery_time'] = order_detail.delivery_time
        #         __dict['status'] = order_detail.status
        #         __dict['max_delivery_time'] = order_detail.max_delivery_time
        #         __dict['commission'] = order_detail.commission
        #         __dict['due_time'] = order_detail.due_time
        #         __dict['due_desc'] = order_detail.due_desc
        #         result.append(__dict)
        #     _dict['sub_order'] = result
        #     data.append(_dict)
        response = APIResponse(success=True, data=data, msg='所有订单信息')
        response[CONTENT_RANGE] = '{0}-{1}'.format(offset, len(orders) - 1)
        response[CONTENT_TOTAL] = total
        return response

    def get_object(self):
        # 1:　子订单　2: 母订单
        order_type = safe_int(self.request.query_params.get('order_type', 1))
        if order_type == 2:
            return Order.objects.get(pk=self.kwargs.get('pk', 0))
        return OrderDetail.objects.get(pk=self.kwargs.get('pk', 0))

    def retrieve(self, request, *args, **kwargs):

        try:
            instance = self.get_object()
        except Exception as e:

            response = APIResponse(success=False, data={}, msg='传入参数有误')
            return response
        if isinstance(instance, Order):
            data = superuser_get_order_detail(instance)
            response = APIResponse(success=True, data=data, msg='%s号母订单信息' % self.kwargs.get('pk', 0))
            return response
        order = Order.objects.get(pk=instance.order)
        data = superuser_get_order_detail(order, son_id=instance.id)
        response = APIResponse(success=True, data=data, msg='%s号子订单信息' % self.kwargs.get('pk', 0))
        return response
        # data = {}
        # orders = Order.objects.filter(pk=id)
        # if orders:
        # order = orders[0]
        # data['id'] = order.id
        # receipt = Receipt.objects.get(pk=order.receipt)
        # data['title'] = receipt.title
        # data['account'] = receipt.account
        # data['tax_number'] = receipt.tax_number
        # data['telephone'] = receipt.telephone
        # data['bank'] = receipt.bank
        # data['company_address'] = receipt.company_address
        # data['receipt_type'] = receipt.receipt_type
        # data['add_time'] = receipt.add_time
        # data['guest_id'] = order.guest_id
        # data['order_sn'] = order.order_sn
        # data['receiver'] = order.receiver
        # data['mobile'] = order.mobile
        # data['address'] = order.address
        # data['remarks'] = order.remarks
        # data['total_money'] = order.total_money
        # order_details = OrderDetail.objects.filter(order=order.id)
        # result = []
        # for order_detail in order_details:
        #     __dict = {}
        #     __dict['son_order_sn'] = order_detail.son_order_sn
        #     __dict['supplier_id'] = order_detail.supplier_id
        #     __dict['goods_id'] = order_detail.goods_id
        #     __dict['model'] = order_detail.model
        #     __dict['brand'] = order_detail.brand
        #     __dict['number'] = order_detail.number
        #     __dict['univalent'] = order_detail.univalent
        #     __dict['subtotal_money'] = order_detail.subtotal_money
        #     __dict['price_discount'] = order_detail.price_discount
        #     __dict['delivery_time'] = order_detail.delivery_time
        #     __dict['status'] = order_detail.status
        #     __dict['max_delivery_time'] = order_detail.max_delivery_time
        #     __dict['commission'] = order_detail.commission
        #     __dict['due_time'] = order_detail.due_time
        #     __dict['due_desc'] = order_detail.due_desc
        #     _result = []
        #     for operation in OrderOperationRecord.objects.filter(order_sn=order_detail.son_order_sn):
        #         _dict = {}
        #         _dict['status'] = operation.status
        #         _dict['operator'] = operation.operator
        #         _dict['execution_detail'] = operation.execution_detail
        #         _dict['progress'] = operation.progress
        #         _dict['time_consuming'] = operation.time_consuming
        #         _dict['add_time'] = operation.add_time
        #         _result.append(_dict)
        #     payment = OrderPayment.objects.filter(order_sn=order_detail.son_order_sn).order_by('-add_time')[0]
        #     __dict['pay_status'] = payment.pay_status
        #     __dict['pay_type'] = payment.pay_type
        #     __dict['operation'] = _result
        #     result.append(__dict)
        # data['sub_order'] = result
        # response = APIResponse(success=True, data=data, msg='%s号订单信息' % id)
        # return response
        # else:
        #     response = APIResponse(success=False, data={}, msg='传入ID有误')
        #     return response

    def update(self, request, *args, **kwargs):
        is_type = safe_int(self.request.data.get('is_type', 0))
        order_sn = self.request.data.get('order_sn', 0)
        user_id = self.request.data.get('user_id', 0)
        if is_type in [0, '0', '']:
            response = APIResponse(success=False, data={}, msg='动作有误')
            return response
        order_detail = OrderDetail.objects.filter(son_order_sn=order_sn)
        if not order_detail:
            response = APIResponse(success=False, data={}, msg='订单号有误')
            return response
        now = datetime.now()
        order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
        time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
        if int(is_type) == 1:
            """取消订单"""
            responsible_party = self.request.data.get('responsible_party', 0)
            cancel_desc = self.request.data.get('cancel_desc', '')
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=2)
            order_detail[0].status = 2
            order_detail[0].save()
            OrderOperationRecord.objects.create(order_sn=order_sn, status=3,
                                                operator=order_detail[0].supplier_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]取消操作' %
                                                                 (order_detail[0].supplier_id, order_sn),
                                                progress='取消订单', time_consuming=time_consuming)
            OrderCancel.objects.create(order_sn=order_sn, responsible_party=responsible_party, cancel_desc=cancel_desc)
            response = APIResponse(success=True, data={}, msg='取消订单操作成功')
            return response
        elif int(is_type) == 2:
            """延期发货"""
            # due_time = self.request.data.get('due_time', '')
            remarks = self.request.data.get('remarks', '')
            original_delivery_time = self.request.data.get('original_delivery_time', '')
            expect_date_of_delivery = self.request.data.get('expect_date_of_delivery', '')
            responsible_party = self.request.data.get('responsible_party', 0)
            order_payment = OrderPayment.objects.filter(order_sn=order_sn).order_by('-add_time')
            if order_payment[0].pay_status == 1:
                response = APIResponse(success=False, data={}, msg='该订单未付款，请先执行付款操作')
                return response
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=8)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=9, operator=0, time_consuming=time_consuming,
                                                execution_detail="超级管理员[%s]更新订单[%s]延期时间" % (user_id, order_sn),
                                                progress='已支付')
            try:
                abnormal_order = AbnormalOrder.objects.get(order_sn=order_sn, abnormal_type=2)
                abnormal_order.is_deal = 2
                abnormal_order.remarks = remarks
                abnormal_order.responsible_party = responsible_party
                abnormal_order.original_delivery_time = original_delivery_time
                abnormal_order.expect_date_of_delivery = expect_date_of_delivery
                abnormal_order.save()
            except Exception as e:
                AbnormalOrder.objects.create(order_sn=order_sn, abnormal_type=2, remarks=remarks, is_deal=2,
                                             original_delivery_time=original_delivery_time,
                                             responsible_party=responsible_party,
                                             expect_date_of_delivery=expect_date_of_delivery)
            expect_date_of_delivery = datetime.strptime(expect_date_of_delivery, '%Y-%m-%d')
            order_detail[0].due_time = expect_date_of_delivery + timedelta(days=order_detail[0].max_delivery_time)
            order_detail[0].due_desc = remarks
            order_detail[0].status = 8
            order_detail[0].save()
            response = APIResponse(success=True, data={}, msg='延期发货操作成功')
            return response
        elif int(is_type) == 3:
            """确认收货"""
            now = datetime.now()
            time_consuming = float(now.timestamp() - order_detail[0].add_time.timestamp())
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=6)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=7,
                                                operator=user_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]确认收货操作' % (user_id, order_sn),
                                                progress='已收货', time_consuming=time_consuming)
            order_detail[0].status = 6
            order_detail[0].save()
            response = APIResponse(success=True, data={}, msg='确认收货操作成功')
            return response
        elif int(is_type) == 4:
            """发货"""
            now = datetime.now()
            order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
            time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=5)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=6,
                                                operator=order_detail.supplier_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]发货操作' %
                                                                 (order_detail.supplier_id, order_sn),
                                                progress='已发货', time_consuming=time_consuming)
            order_detail.status = 5
            order_detail.save()
            response = APIResponse(success=True, data={}, msg='发货操作成功')
            return response
        elif int(is_type) == 5:
            """支付"""
            trade_no = self.request.data.get('trade_no', '')
            pay_type = self.request.data.get('pay_type', '')
            guest_id = user_id
            SuperUserOperation.objects.create(order_sn=order_sn, operator=guest_id,
                                              original_status=order_detail[0].status, changed_status=3)
            OrderPayment.objects.create(order_sn=order_sn, pay_type=pay_type, trade_no=trade_no, pay_status=2)
            order_detail.status = 3
            OrderOperationRecord.objects.create(order_sn=order_sn, status=2, operator=guest_id,
                                                execution_detail='超级管理员[%s]对订单[%s]执行支付操作,使用[%s]方式支付' % (
                                                    user_id, order_sn, PAY_TYPE[pay_type]), progress='已支付')
            # # 创建一条系统记录
            # OrderOperationRecord.objects.create(order_sn=order_sn, status=4, operator=0,
            #                                     execution_detail='接单提醒', progress='已支付')
            order_detail.save()
            response = APIResponse(success=True, data={}, msg='支付操作成功')
            return response
        elif int(is_type) == 6:
            """无货"""
            remarks = self.request.data.get('remarks', '')
            responsible_party = self.request.data.get('responsible_party', 0)
            order_detail = order_detail[0]
            now = datetime.now()
            order_operation = OrderOperationRecord.objects.filter(order_sn=order_sn).order_by('-add_time')
            time_consuming = float(now.timestamp() - order_operation[0].add_time.timestamp())
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail.status, changed_status=13)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=16,
                                                operator=order_detail.supplier_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]无货操作' % (user_id, order_sn),
                                                progress='待接单,无货', time_consuming=time_consuming)
            # 存在该异常订单就修改原订单  否则新建新的订单
            try:
                abnormal_order = AbnormalOrder.objects.get(order_sn=order_sn, abnormal_type=1)
                abnormal_order.is_deal = 2
                abnormal_order.responsible_party = responsible_party
                abnormal_order.remarks = remarks
                abnormal_order.save()
            except Exception as e:
                AbnormalOrder.objects.create(order_sn=order_sn, abnormal_type=1, remarks=remarks, is_deal=2,
                                             responsible_party=responsible_party)
            order_detail.status = 13
            order_detail.save()

            # 执行退款逻辑
            headers = {'content-type': 'application/json',
                       'user-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
            parameters = json.dumps({'order_sn': order_detail.returns_sn})
            try:
                response = requests.post(ORDER_API_HOST + '/api/refund', data=parameters, headers=headers)
                response_dict = json.loads(response.text)
            except Exception as e:
                logger.info('ID生成器连接失败!!!')
                response = APIResponse(success=False, data={}, msg='ID生成器连接失败!!!')
                return response
            refund_sn = response_dict['data']['tk_order_id']
            OrderRefund.objects.create(order_sn=order_detail.son_order_sn, refund_sn=refund_sn,
                                       amount=order_detail.subtotal_money, status=1)
            OrderOperationRecord.objects.create(order_sn=order_detail.order_sn, status=11,
                                                operator=0,
                                                execution_detail='系统自动生成退款单',
                                                progress='退款中', time_consuming=time_consuming)
            # 后边调用退款接口
            pass
            response = APIResponse(success=True, data={}, msg='无货操作成功')
            return response
        elif int(is_type) == 7:
            """接单"""
            supplier_id = self.request.data.get['supplier_id']
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=4)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=5,
                                                operator=supplier_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]接单操作' %
                                                                 (supplier_id, order_sn),
                                                progress='已接单', time_consuming=time_consuming)
            order_detail.status = 4
            order_detail.save()
            response = APIResponse(success=True, data={}, msg='接单操作成功')
            return response
        elif int(is_type) == 8:
            """退货"""
            remarks = self.request.data.get('remarks', '')
            try:
                return_deal = ReturnsDeal.objects.get(order_sn=order_sn, return_type=1)
                return_deal.is_deal = 2
                return_deal.save()
            except Exception:
                ReturnsDeal.objects.create(order_sn=order_sn, is_deal=2, remarks=remarks)
            SuperUserOperation.objects.create(order_sn=order_sn, operator=user_id,
                                              original_status=order_detail[0].status, changed_status=11)
            OrderOperationRecord.objects.create(order_sn=order_sn, status=13, operator=user_id,
                                                execution_detail='超级管理员[%s]执行订单[%s]同意退货操作' %
                                                                 (user_id, order_sn),
                                                progress='同意退货', time_consuming=time_consuming)
            order_detail[0].status = 11
            order_detail[0].save()
            response = APIResponse(success=True, data={}, msg='同意退货')
            return response
        else:
            response = APIResponse(success=False, data={}, msg='未定义动作')
            return response

    def create(self, request, *args, **kwargs):
        response = generation_order(request.data['data'])
        return response

    def get_serializer_class(self):
        if self.action == 'update':
            return SuperUserUpdateSerializer
        elif self.action == 'create':
            return OrderSerializer
        return UserOrderSerializer


class OrderFinanceViewSet(viewsets.ViewSet):

    def retrieve(self, request, pk):
        order_sn = pk
        is_son_order = False
        # 0: 支付   1 退款
        is_type = safe_int(request.query_params.get('is_type'))
        amount = safe_float(request.query_params.get('amount'))
        try:
            order = Order.objects.get(order_sn=order_sn)
        except Exception:
            order = OrderDetail.objects.filter(son_order_sn=order_sn)
            is_son_order = True
        if not order:
            response = APIResponse(success=False, data={}, msg='传入订单号有误')
            return response
        if is_son_order:
            if not is_type:
                response = APIResponse(success=False, data={}, msg='子订单不允许单个支付')
                return response
            order = order[0]
            payment = OrderPayment.objects.filter(order_sn=order.son_order_sn).order_by('-add_time')
            if not payment:
                response = APIResponse(success=False, data={}, msg='该订单没有创建初始支付信息,请联系管理员')
                return response
            payment = payment[0]
            if payment.pay_status != 2:
                response = APIResponse(success=False, data={}, msg='该订单尚未执行支付操作,无法退款')
                return response
            if order.subtotal_money != amount:
                response = APIResponse(success=False, data={},
                                       msg='退款金额不对, 应退[%s],实退[%s]' % (order.subtotal_money, amount))
                return response
            response = APIResponse(success=True, data={}, msg='核对成功')
            return response
        else:
            if is_type != 0:
                response = APIResponse(success=False, data={}, msg='传入参数有误')
                return response
            payment = OrderPayment.objects.filter(order_sn=order.order_sn).order_by('-add_time')
            if not payment:
                response = APIResponse(success=False, data={}, msg='该订单没有创建初始支付信息,请联系管理员')
                return response
            payment = payment[0]
            if payment.pay_status == 2:
                response = APIResponse(success=False, data={}, msg='该订单已经支付过,无需重复支付')
                return response
        if order.total_money != amount:
            response = APIResponse(success=False, data={}, msg='该订单支付金额有误,应支付[%s],实付[%s]' % (order.total_money,
                                                                                             amount))
            return response
        response = APIResponse(success=True, data={}, msg='核对成功')
        return response
