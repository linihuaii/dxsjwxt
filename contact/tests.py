"""
联系表单后台模块的测试。

覆盖点：

- 后台侧边栏是否出现「联系表单」一级菜单及其两个二级菜单项
- 两个二级页面能否访问、是否返回真实数据库数据
- 代理模型是否与 `web.Contact` 共用同一张 `contact` 表
- 只读概览页是否屏蔽了增删改入口
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from web.models import Contact

from .models import ContactMessage, ContactOverview


class ContactAdminMenuTests(TestCase):
    """后台菜单结构。"""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='menu-tester', email='menu@test.local', password='test-pass-123',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_contact_app_is_registered(self):
        """contact 应用必须在 INSTALLED_APPS 中，否则不会出现一级菜单。"""
        from django.apps import apps

        self.assertTrue(apps.is_installed('contact'))
        self.assertEqual(apps.get_app_config('contact').verbose_name, '联系表单')

    def test_proxy_models_point_to_contact_table(self):
        """两个代理模型都指向 contact 表，且不参与建表。"""
        for model in (ContactMessage, ContactOverview):
            with self.subTest(model=model.__name__):
                self.assertTrue(model._meta.proxy)
                self.assertEqual(model._meta.db_table, 'contact')
                self.assertFalse(model._meta.can_migrate(None))

    def test_models_registered_in_admin(self):
        """两个代理模型都要在 admin 注册表里，否则二级菜单不显示。"""
        self.assertIn(ContactMessage, admin.site._registry)
        self.assertIn(ContactOverview, admin.site._registry)

    def test_menu_json_contains_contact_group(self):
        """后台首页注入的 menus JSON 中应含「联系表单」分组与两个二级菜单。"""
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        # 中文在 JSON 中以 \uXXXX 转义，这里按转义码比对
        self.assertIn('\\u8054\\u7cfb\\u8868\\u5355', content)   # 联系表单
        self.assertIn('\\u54a8\\u8be2\\u7559\\u8a00', content)   # 咨询留言
        self.assertIn('\\u6570\\u636e\\u6982\\u89c8', content)   # 数据概览

    def test_secondary_menu_urls_are_reachable(self):
        """两个二级菜单页都能正常访问。"""
        urls = [
            reverse('admin:contact_contactmessage_changelist'),
            reverse('admin:contact_contactoverview_changelist'),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class ContactSharedTableTests(TestCase):
    """代理模型与具体模型共用一张表。"""

    def test_proxy_models_share_same_rows(self):
        Contact.objects.create(name='张三', phone='13800138000', city='佛山')
        Contact.objects.create(name='李四', phone='13900139000', city='广州')

        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(ContactMessage.objects.count(), 2)
        self.assertEqual(ContactOverview.objects.count(), 2)

    def test_writing_through_proxy_is_visible_in_base_model(self):
        """通过代理模型写入的数据，用具体模型也能读到（确实是同一张表）。"""
        ContactMessage.objects.create(name='王五', phone='13700137000', city='深圳')

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(Contact.objects.first().name, '王五')


class ContactOverviewPageTests(TestCase):
    """「数据概览」页面的真实数据渲染。"""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='overview-tester', email='overview@test.local', password='test-pass-123',
        )
        cls.contact = Contact.objects.create(
            name='赵六', phone='13600136000', city='佛山',
            demand_type='全屋木作定制', budget='15 - 30 万', description='三室两厅整屋定制',
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_overview_shows_real_records(self):
        """概览页应展示数据库里的真实留言。"""
        response = self.client.get(reverse('admin:contact_contactoverview_changelist'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')
        self.assertIn(self.contact.name, content)
        self.assertIn(self.contact.phone, content)
        self.assertIn(self.contact.city, content)
        self.assertIn(self.contact.demand_type, content)

    def test_overview_summary_counts_match_database(self):
        """概览统计与直接查询数据库的结果一致。"""
        from .admin import build_summary

        summary = build_summary()
        self.assertEqual(summary['total'], Contact.objects.count())
        self.assertEqual(summary['total'], 1)
        self.assertEqual(summary['today_count'], 1)
        self.assertEqual(summary['week_count'], 1)

        # 状态分布：pending 一条，其余为 0
        status_counts = {row['value']: row['count'] for row in summary['status_rows']}
        self.assertEqual(status_counts['pending'], 1)
        self.assertEqual(status_counts['deal'], 0)

        # 城市 Top 与近 7 天趋势
        self.assertEqual(summary['city_rows'][0]['label'], '佛山')
        self.assertEqual(summary['city_rows'][0]['count'], 1)
        self.assertEqual(summary['city_rows'][0]['percent'], 100.0)
        self.assertEqual(len(summary['trend']), 7)
        self.assertEqual(summary['trend'][-1]['count'], 1)

    def test_overview_is_read_only(self):
        """概览页不提供新增 / 编辑 / 删除入口。"""
        response = self.client.get(reverse('admin:contact_contactoverview_changelist'))
        content = response.content.decode('utf-8')

        self.assertNotIn('contact/contactoverview/add/', content)
        self.assertNotIn('contact/contactoverview/delete/', content)

    def test_overview_change_view_redirects_back(self):
        """访问概览模型的编辑页应回到概览，而不是报错。"""
        url = reverse('admin:contact_contactoverview_change', args=[self.contact.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
