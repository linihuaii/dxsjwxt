"""
接口测试

用 `python manage.py test web` 运行，覆盖：

  - 统一响应信封格式
  - CSRF 防护（公开提交接口同样受保护）
  - 字段校验与中文报错
  - 公开接口与管理员接口的权限边界
  - 限流策略
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from .models import Contact


class ContactApiTests(TestCase):
    """咨询留言接口测试。"""

    def setUp(self):
        cache.clear()
        # enforce_csrf_checks=True 才会真正走 CSRF 校验
        self.client = Client(enforce_csrf_checks=True)
        # 测试库是全新的，超级管理员不存在，这里现建一个
        self.user = get_user_model().objects.create_superuser(
            username='linihuaii',
            password='123456',
            email='2411557902@qq.com',
        )

    # ------------------------------------------------------------------ 工具
    def csrf_token(self):
        """取一个 CSRF token，供后续 POST 使用。"""
        response = self.client.get('/api/csrf/')
        return response.json()['data']['csrfToken']

    def post_contact(self, payload, token=None):
        return self.client.post(
            '/api/contacts/',
            payload,
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token if token is not None else self.csrf_token(),
        )

    def payload(self, **overrides):
        data = {
            'name': '张先生',
            'phone': '138 0013 8000',
            'city': '佛山',
            'demand_type': '全屋木作定制',
            'budget': '15 - 30 万',
            'description': '三室两厅 89 平，想要整屋原木定制。',
        }
        data.update(overrides)
        return data

    # ------------------------------------------------------------ API 索引
    def test_api_index(self):
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(len(body['data']['endpoints']), 5)

    # ---------------------------------------------------------------- CSRF
    def test_csrf_endpoint_returns_token_and_cookie(self):
        response = self.client.get('/api/csrf/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['csrfToken'])
        self.assertIn('csrftoken', response.cookies)

    def test_submit_without_csrf_is_rejected(self):
        """公开接口同样受 CSRF 保护，跨站伪造提交会被拦下。"""
        response = self.client.post(
            '/api/contacts/', self.payload(),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Contact.objects.count(), 0)

    # ---------------------------------------------------------------- 提交
    def test_submit_creates_contact(self):
        response = self.post_contact(self.payload())
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['code'], 'created')
        self.assertIn('反馈已提交', body['message'])
        self.assertEqual(Contact.objects.count(), 1)

        saved = Contact.objects.first()
        self.assertEqual(saved.name, '张先生')
        self.assertEqual(saved.phone, '138 0013 8000')
        self.assertEqual(saved.demand_type, '全屋木作定制')
        self.assertEqual(saved.budget, '15 - 30 万')
        self.assertEqual(saved.status, 'pending')

    def test_submit_response_contains_all_fields(self):
        response = self.post_contact(self.payload())
        data = response.json()['data']
        for field in ['id', 'name', 'phone', 'city', 'demand_type',
                      'budget', 'description', 'status', 'created_at']:
            self.assertIn(field, data)

    def test_status_cannot_be_forged_by_visitor(self):
        """访客即使在请求体里塞 status 也会被忽略。"""
        self.post_contact(self.payload(name='恶意', status='deal'))
        self.assertEqual(Contact.objects.get(name='恶意').status, 'pending')

    # ---------------------------------------------------------------- 校验
    def test_missing_required_field(self):
        response = self.post_contact({'phone': '13800138000'})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['success'])
        self.assertEqual(body['code'], 'validation_error')
        self.assertIn('name', body['errors'])
        self.assertIn('必填', body['errors']['name'][0])

    def test_invalid_phone(self):
        response = self.post_contact(self.payload(phone='abc'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.json()['errors'])
        self.assertIn('联系电话', response.json()['errors']['phone'][0])

    def test_invalid_choice(self):
        response = self.post_contact(self.payload(demand_type='不存在的类型'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('demand_type', response.json()['errors'])
        self.assertIn('合法选项', response.json()['errors']['demand_type'][0])

    def test_valid_choices_accepted(self):
        response = self.post_contact(self.payload(demand_type='到厂参观', budget='暂不确定'))
        self.assertEqual(response.status_code, 201)

    # ---------------------------------------------------------------- 权限
    def test_list_requires_admin(self):
        response = self.client.get('/api/contacts/')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

    def test_admin_can_list(self):
        Contact.objects.create(name='李女士', phone='13800138000')
        self.client.force_login(self.user)
        response = self.client.get('/api/contacts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), Contact.objects.count())

    def test_detail_requires_admin(self):
        contact = Contact.objects.create(name='李女士', phone='13800138000')
        self.assertEqual(self.client.get(f'/api/contacts/{contact.id}/').status_code, 403)

        self.client.force_login(self.user)
        response = self.client.get(f'/api/contacts/{contact.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['id'], contact.id)

    # ---------------------------------------------------------------- 更新
    def test_admin_can_update_status(self):
        contact = Contact.objects.create(name='李女士', phone='13800138000')
        self.client.force_login(self.user)
        response = self.client.patch(
            f'/api/contacts/{contact.id}/',
            {'status': 'followed'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], 'followed')
        contact.refresh_from_db()
        self.assertEqual(contact.status, 'followed')

    def test_update_rejects_invalid_status(self):
        contact = Contact.objects.create(name='李女士', phone='13800138000')
        self.client.force_login(self.user)
        response = self.client.patch(
            f'/api/contacts/{contact.id}/',
            {'status': '不存在的状态'},
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.csrf_token(),
        )
        self.assertEqual(response.status_code, 400)

    # ---------------------------------------------------------------- 边界
    def test_method_not_allowed(self):
        response = self.client.put('/api/contacts/', {}, content_type='application/json')
        self.assertEqual(response.status_code, 405)
        self.assertIn('请求方式', response.json()['message'])

    def test_missing_record_returns_404_for_admin(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/contacts/999999/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('不存在', response.json()['message'])

    def test_legacy_hello_endpoint_still_works(self):
        self.assertEqual(self.client.get('/api/hello/').status_code, 200)

    # ---------------------------------------------------------------- 限流
    def test_submit_is_rate_limited(self):
        token = self.csrf_token()
        codes = [
            self.post_contact(self.payload(name=f'批量{i}'), token=token).status_code
            for i in range(25)
        ]
        self.assertEqual(codes[:20].count(201), 20)
        self.assertEqual(codes[20], 429)

        response = self.post_contact(self.payload(name='再来一次'), token=token)
        body = response.json()
        self.assertEqual(response.status_code, 429)
        self.assertIn('频繁', body['message'])
        self.assertIn('秒后再试', body['message'])

