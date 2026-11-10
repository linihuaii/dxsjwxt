"""
联系表单的后台管理视图。

对应后台侧边栏的结构：

    联系表单          ← 一级菜单（App 分组，名称取自 ContactConfig.verbose_name）
      ├── 咨询留言     ← 二级菜单：ContactMessage 的常规增删改查列表
      └── 数据概览     ← 二级菜单：ContactOverview，现场聚合 contact 表的统计页

两个模型都是 `web.Contact` 的代理模型，共享同一张 `contact` 表，
因此后台里看到的就是线上真实的咨询留言，不会产生第二份数据。
"""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils import timezone

from web.models import Contact

from .models import ContactMessage, ContactOverview


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """咨询留言列表 —— 与 web.ContactAdmin 指向同一张 contact 表。"""

    list_display = ['name', 'phone', 'city', 'demand_type', 'budget', 'status', 'created_at']
    list_display_links = ['name', 'phone']
    list_filter = ['status', 'demand_type', 'budget', 'created_at']
    search_fields = ['name', 'phone', 'city', 'description']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    list_per_page = 20
    readonly_fields = ['created_at']
    fieldsets = [
        ('反馈人信息', {
            'fields': ['name', 'phone', 'city'],
        }),
        ('需求内容', {
            'fields': ['demand_type', 'budget', 'description'],
        }),
        ('跟进信息', {
            'fields': ['status', 'created_at'],
        }),
    ]


@admin.register(ContactOverview)
class ContactOverviewAdmin(admin.ModelAdmin):
    """
    数据概览 —— 一个纯查询页面。

    它是代理模型，不存任何数据；页面内容全部由这里现场查询
    contact 表得到（总数、状态分布、需求类型分布、预算分布、
    近 7 天趋势、城市 Top、最近提交），看到的永远是真实数据。
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        # 概览是只读页，能进后台就能看，不需要额外的模型权限
        return request.user.is_active and request.user.is_staff

    def changelist_view(self, request, extra_context=None):
        """直接渲染概览页，跳过 Django 默认的列表页。"""
        context = {
            **self.admin_site.each_context(request),
            'title': '数据概览',
            'opts': self.model._meta,
            'summary': build_summary(),
            'has_permission': True,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/contact/overview.html', context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """概览页面没有编辑入口，一律回到概览。"""
        return self.changelist_view(request)


def build_summary():
    """
    现场查询 contact 表，生成概览页所需的统计数据。

    全部使用 ORM 聚合，查询的是真实数据，不含任何写死的内容。
    """
    qs = Contact.objects.all()

    # 总量
    total = qs.count()

    # 按处理状态分布
    status_rows = []
    for value, label in Contact.STATUS_CHOICES:
        count = qs.filter(status=value).count()
        status_rows.append({
            'label': label,
            'value': value,
            'count': count,
            'percent': round(count * 100 / total, 1) if total else 0.0,
        })

    # 按需求类型分布
    demand_rows = [
        {
            'label': row['demand_type'] or '未选择',
            'count': row['count'],
            'percent': round(row['count'] * 100 / total, 1) if total else 0.0,
        }
        for row in qs.values('demand_type').annotate(count=Count('id')).order_by('-count')
    ]

    # 按预算区间分布
    budget_rows = [
        {
            'label': row['budget'] or '未选择',
            'count': row['count'],
            'percent': round(row['count'] * 100 / total, 1) if total else 0.0,
        }
        for row in qs.values('budget').annotate(count=Count('id')).order_by('-count')
    ]

    # 所在城市 Top 5
    city_rows = [
        {
            'label': row['city'] or '未填写',
            'count': row['count'],
            'percent': round(row['count'] * 100 / total, 1) if total else 0.0,
        }
        for row in qs.exclude(city='').values('city').annotate(count=Count('id')).order_by('-count')[:5]
    ]

    # 近 7 天提交趋势
    today = timezone.localdate()
    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        trend.append({
            'date': day,
            'label': f'{day.month}/{day.day}',
            'count': qs.filter(created_at__date=day).count(),
        })

    # 柱高按近 7 天峰值等比换算（像素），避免量纲混乱
    peak = max((item['count'] for item in trend), default=0)
    for item in trend:
        item['height_px'] = round(item['count'] * 118 / peak) if peak else 0

    # 最近提交的 5 条
    recent = list(qs.order_by('-created_at')[:5])

    # 今日 / 近 7 天新增
    today_count = qs.filter(created_at__date=today).count()
    week_count = qs.filter(created_at__date__gte=today - timedelta(days=6)).count()

    return {
        'total': total,
        'status_rows': status_rows,
        'demand_rows': demand_rows,
        'budget_rows': budget_rows,
        'city_rows': city_rows,
        'trend': trend,
        'recent': recent,
        'today_count': today_count,
        'week_count': week_count,
    }
