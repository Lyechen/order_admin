"""order_admin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# import xadmin
from django.urls import path, include
# from xadmin.plugins import xversion
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.documentation import include_docs_urls

from orders.views import OrderViewSet, OrderCancelViewSet, OrderPaymentViewSet, ChiefOrderViewSet
from orders.views import OrderLogisticsViewSet, ReceiptViewSet, AbnormalOrderViewSet, SupperUserViewSet
from orders.views import AdminOrderCancelViewSet, MyOrderViewSet, SupplierOrderAdminViewSet, OrderFinanceViewSet

# xadmin.autodiscover()
# xversion.register_models()

route = DefaultRouter(trailing_slash=False)
# 提交订单
route.register('user/order', OrderViewSet, base_name='user/order')
# 订单取消(用户)
# route.register('cancel', OrderCancelViewSet, base_name='cancel')
# 支付
# route.register('payment', OrderPaymentViewSet, base_name='payment')
# 运营订单
route.register('chief/order', ChiefOrderViewSet, base_name='chief/order')
# 订单取消(运营后台)
# route.register('order_cancel', AdminOrderCancelViewSet, base_name='order_cancel')
# 我的订单
# route.register('my_order', MyOrderViewSet, base_name='my_order')
# 供应商订单
route.register('supplier/order', SupplierOrderAdminViewSet, base_name='supplier/order')
# 订单物流
route.register('order/logistics', OrderLogisticsViewSet, base_name='order/logistics')
# 发票相关
route.register('order/receipt', ReceiptViewSet, base_name='receipt')
# 异常订单
# route.register('abnormal_order', AbnormalOrderViewSet, base_name='abnormal_order')
# 超级管理员入口,这将是fix_bug的存在
route.register('superuser/order', SupperUserViewSet, base_name='super/order')
# 供财务系统验证的接口
route.register('order/finance', OrderFinanceViewSet, base_name='order/finance')

urlpatterns = [
    # path('xadmin/', xadmin.site.urls),
    path('v1/', include(route.urls)),
    path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(r'docs/', include_docs_urls(title='订单管理')),
    # path(r'login', obtain_jwt_token),
]
