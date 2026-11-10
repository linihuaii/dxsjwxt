"""
web 应用的后台注册。

`contact` 表的后台管理入口统一放在 `contact` 应用里，
由 `contact.admin.ContactMessageAdmin` 提供，
这样后台侧边栏才会以「联系表单」作为一级菜单分组，
不会出现两个「咨询留言」入口。
"""

from django.contrib import admin  # noqa: F401  确保模块被 admin 自动发现
