"""
联系表单的后台模型。

这里定义的两个模型都是**代理模型**（`proxy = True`）：

- `ContactMessage`   复用 `web.Contact` 的 `contact` 表，承载「咨询留言」二级菜单
- `ContactOverview`  同样复用该表，承载「数据概览」二级菜单

代理模型不建表、不存数据，Django 会自动把目标模型的 `db_table`（即 `contact`）
复制过来，因此后台读到的永远是 `contact` 表里的真实留言。

注意：Django 在构建模型类时会把 `Meta` 从类属性中 `pop` 掉，
所以这里无法用 `class Meta(ContactBase.Meta)` 继承，必须完整重写一遍。
"""

from django.db import models

from web.models import Contact as ContactBase


class ContactMessage(ContactBase):
    """咨询留言（后台「联系表单 → 咨询留言」）。"""

    class Meta:
        proxy = True
        db_table = 'contact'
        verbose_name = '咨询留言'
        verbose_name_plural = '咨询留言'
        ordering = ['-created_at']


class ContactOverview(ContactBase):
    """数据概览（后台「联系表单 → 数据概览」）。

    本身不存数据，只作为「数据概览」页面的挂载点，
    页面内容由 ContactOverviewAdmin 现场查询 contact 表生成。
    """

    class Meta:
        proxy = True
        db_table = 'contact'
        verbose_name = '数据概览'
        verbose_name_plural = '数据概览'
        ordering = ['-created_at']

    def __str__(self):
        return '联系表单数据概览'
