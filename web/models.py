"""
数据模型

当前只有一个模型：Contact —— 对应官网「联系」页面的咨询表单。
表名固定为 contact，与前端表单字段一一对应。
"""

from django.core.validators import RegexValidator
from django.db import models

# 联系电话：允许数字、空格、+、-、括号，可覆盖手机 / 座机 / 带区号写法
phone_validator = RegexValidator(
    regex=r'^[\d\s+\-()]{6,20}$',
    message='请输入有效的联系电话（6-20 位，可含数字、空格、+、- 与括号）',
)


class Contact(models.Model):
    """客户咨询留言，对应联系页面的在线留言表单。"""

    # 需求类型：取值与前端 ContactPage.vue 的 demandTypes 完全一致
    DEMAND_TYPE_CHOICES = [
        ('标准产品咨询', '标准产品咨询'),
        ('全屋木作定制', '全屋木作定制'),
        ('单件家具定制', '单件家具定制'),
        ('软装配饰搭配', '软装配饰搭配'),
        ('商业空间定制', '商业空间定制'),
        ('到厂参观', '到厂参观'),
    ]

    # 预算区间：取值与前端 ContactPage.vue 的 budgets 完全一致
    BUDGET_CHOICES = [
        ('5 万以内', '5 万以内'),
        ('5 - 15 万', '5 - 15 万'),
        ('15 - 30 万', '15 - 30 万'),
        ('30 - 50 万', '30 - 50 万'),
        ('50 万以上', '50 万以上'),
        ('暂不确定', '暂不确定'),
    ]

    # 处理状态：后台回访跟进时使用
    STATUS_CHOICES = [
        ('pending', '待跟进'),
        ('followed', '已联系'),
        ('deal', '已成交'),
        ('invalid', '无效需求'),
    ]

    name = models.CharField(
        '称呼', max_length=50,
        help_text='客户称呼，例如「张先生」',
    )
    phone = models.CharField(
        '联系电话', max_length=20,
        validators=[phone_validator],
        help_text='用于回访的联系电话',
    )
    city = models.CharField(
        '所在城市', max_length=50, blank=True,
        help_text='例如「佛山」',
    )
    demand_type = models.CharField(
        '需求类型', max_length=20, blank=True,
        choices=DEMAND_TYPE_CHOICES,
        help_text='留空表示客户未选择',
    )
    budget = models.CharField(
        '预算区间', max_length=20, blank=True,
        choices=BUDGET_CHOICES,
        help_text='留空表示客户未选择',
    )
    description = models.TextField(
        '需求描述', blank=True,
        help_text='客户的补充说明',
    )
    status = models.CharField(
        '处理状态', max_length=10, default='pending',
        choices=STATUS_CHOICES,
    )
    created_at = models.DateTimeField('提交时间', auto_now_add=True)

    class Meta:
        db_table = 'contact'
        verbose_name = '咨询留言'
        verbose_name_plural = '咨询留言'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}（{self.phone}）'
