# _*_ coding:utf-8 _*_
__author__ = 'jiangchao'
from django_filters import rest_framework as filters
from django.db.models.base import Q

from .models import OrderDetail


class UserOrderFilter(filters.FilterSet):
    son_order_sn = filters.CharFilter(name='son_order_sn')
    supplier_id = filters.NumberFilter(name='supplier_id')
    # top_category = filters.NumberFilter(method='top_category_filter')
    #
    # def top_category_filter(self, queryset, name, value):
    #     return queryset.filter(Q(category=value) |
    #                            Q(category__parent_category_id=value) |
    #                            Q(category__parent_category__parent_category_id=value))

    class Meta:
        model = OrderDetail
        fields = ['son_order_sn', 'supplier_id']
