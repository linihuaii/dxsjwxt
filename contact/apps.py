"""
联系表单后台应用。

这个应用不拥有自己的数据表，只用**代理模型**（proxy model）复用
`web.Contact` 的同一张 `contact` 表，作用有两个：

1. 在 Django 后台侧边栏中，把「联系表单」做成一个**独立的一级菜单**
   （后台的一级菜单按 App 分组，二级菜单按模型分组）；
2. 挂载「数据概览」二级菜单，用真实查询统计 contact 表的数据。

代理模型共享原模型的表与字段，所以后台里看到的即是线上真实留言，
既不会产生第二张表，也不会出现两份数据。
"""

from django.apps import AppConfig


class ContactConfig(AppConfig):
    name = 'contact'
    # 后台侧边栏的一级菜单名，simpleui 会直接取这个值
    verbose_name = '联系表单'

    def ready(self):
        """把后台下拉框的空白占位项改成中文。

        Django 6.1 的 `zh_Hans` 语言包未收录 `BLANK_CHOICE_LABEL`
        （"- Select an option -"）这条文案，后台下拉框会显示英文。
        Django 官方给出的覆盖方式就是在应用的 ready() 里改写它，
        这样整个后台的所有下拉框都会生效，而不只是某一个模型。
        """
        from django.db.models import fields

        fields.BLANK_CHOICE_LABEL = '请选择'
