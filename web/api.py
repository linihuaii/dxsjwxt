"""
官网后端 API

接口清单：

    GET    /api/                       API 索引，列出所有可用端点
    GET    /api/csrf/                  获取 CSRF token（前端提交前先取一次）
    POST   /api/contacts/              提交咨询留言 —— 公开
    GET    /api/contacts/              查看留言列表 —— 仅管理员
    GET    /api/contacts/<id>/         查看单条留言 —— 仅管理员
    PATCH  /api/contacts/<id>/         更新留言（如跟进状态）—— 仅管理员

响应统一使用信封格式：

    成功  {"success": true,  "code": "...", "message": "...", "data": {...}}
    失败  {"success": false, "code": "...", "message": "...", "errors": {...}}
"""

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler

from .models import Contact
from .serializers import ContactCreateSerializer, ContactSerializer

# ---------------------------------------------------------------------------
# 统一响应格式
# ---------------------------------------------------------------------------

# 各 HTTP 状态码对应的中文提示。DRF 自带的 zh_Hans 语言包漏掉了
# “Invalid data.” 与 “Not valid.” 两条，这里统一兜住，保证前台拿到的
# 全是中文提示。
ERROR_MESSAGES = {
    400: '提交的信息有误，请检查标红的字段后重试。',
    401: '请先登录后再操作。',
    403: '您没有执行该操作的权限。',
    404: '请求的资源不存在。',
    405: '不支持的请求方式。',
    429: '提交过于频繁，请稍后再试。',
    500: '服务器开小差了，请稍后再试。',
}

# DRF 异常默认文案 → 中文
ERROR_TEXT_MAP = {
    'Invalid data.': '提交的数据有误，请检查后重试。',
    'Not valid.': '数据校验未通过。',
    'You do not have permission to perform this action.': '您没有执行该操作的权限。',
    'Authentication credentials were not provided.': '请先登录后再操作。',
    'Request was throttled.': '提交过于频繁，请稍后再试。',
}


def _translate(text):
    """把 DRF 的英文默认文案替换成中文。"""
    if isinstance(text, str):
        return ERROR_TEXT_MAP.get(text, text)
    return text


def success(data=None, message='操作成功', code='ok', http_status=status.HTTP_200_OK):
    """构造统一格式的成功响应。"""
    return Response(
        {
            'success': True,
            'code': code,
            'message': message,
            'data': data,
        },
        status=http_status,
    )


def failure(message, code='error', errors=None, http_status=status.HTTP_400_BAD_REQUEST):
    """构造统一格式的失败响应。"""
    body = {
        'success': False,
        'code': code,
        'message': message,
    }
    if errors:
        body['errors'] = errors
    return Response(body, status=http_status)


def exception_handler(exc, context):
    """
    DRF 全局异常处理器。

    把 DRF 抛出的各类异常统一转换成中文的信封格式，
    并保证字段级错误信息（errors）保留下来供前端做表单内联提示。
    """
    response = drf_exception_handler(exc, context)

    # 非 DRF 异常（如数据库错误）交给 Django 的默认处理
    if response is None:
        return None

    data = response.data

    if isinstance(data, dict) and 'detail' in data and len(data) == 1:
        # 顶层错误：权限不足、限流、方法不允许等
        detail = _translate(data['detail'])
        message = ERROR_MESSAGES.get(
            response.status_code,
            detail if isinstance(detail, str) else '请求处理失败。',
        )
        if isinstance(exc, Throttled):
            # 限流带上等待秒数，方便前端提示
            wait = getattr(exc, 'wait', None)
            if wait:
                message = f'提交过于频繁，请 {int(wait)} 秒后再试。'
        response.data = {
            'success': False,
            'code': getattr(exc, 'default_code', 'error'),
            'message': message,
        }
        return response

    # 字段级错误：逐字段翻译后保留
    errors = {}
    if isinstance(data, dict):
        for field, messages in data.items():
            if isinstance(messages, (list, tuple)):
                errors[field] = [_translate(m) for m in messages]
            else:
                errors[field] = [_translate(messages)]

    response.data = {
        'success': False,
        'code': 'validation_error',
        'message': ERROR_MESSAGES.get(response.status_code, '提交的数据有误，请检查后重试。'),
        'errors': errors,
    }
    return response


# ---------------------------------------------------------------------------
# 认证
# ---------------------------------------------------------------------------

class CsrfEnforcedSessionAuthentication(SessionAuthentication):
    """
    对匿名请求也强制校验 CSRF。

    DRF 的 `APIView.as_view()` 会对视图做 `csrf_exempt`，而标准
    `SessionAuthentication` 只在**已登录**时才会校验 CSRF。
    公开的提交接口（游客未登录）因此会完全绕过 CSRF 校验，
    任何站点都能跨源伪造提交。

    这里把校验提到最前面，不论是否登录都执行一次，
    保证公开接口同样受 CSRF 保护。
    """

    def authenticate(self, request):
        self.enforce_csrf(request)

        user = getattr(request._request, 'user', None)
        if not user or not user.is_active:
            return None
        return (user, None)


# ---------------------------------------------------------------------------
# 视图
# ---------------------------------------------------------------------------

class ApiIndexView(APIView):
    """API 索引，列出所有可用端点，便于自测与演示。"""

    permission_classes = [AllowAny]
    throttle_scope = 'admin_read'

    def get(self, request):
        return success({
            'name': '课序 项目展示接口',
            'version': '1.0',
            'endpoints': [
                {'method': 'GET', 'path': '/api/csrf/', 'desc': '获取 CSRF token'},
                {'method': 'POST', 'path': '/api/contacts/', 'desc': '提交咨询留言（公开）'},
                {'method': 'GET', 'path': '/api/contacts/', 'desc': '查看留言列表（需管理员登录）'},
                {'method': 'GET', 'path': '/api/contacts/<id>/', 'desc': '查看单条留言（需管理员登录）'},
                {'method': 'PATCH', 'path': '/api/contacts/<id>/', 'desc': '更新留言（需管理员登录）'},
            ],
        })


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfTokenView(APIView):
    """
    下发 CSRF token。

    会同时做两件事：
      1. 通过 `ensure_csrf_cookie` 写入 `csrftoken` Cookie
      2. 在响应体里直接返回 token

    前端两种取法都支持：axios 读 Cookie 自动带上请求头，
    或直接用响应体里的 token 手动塞进 `X-CSRFToken` 请求头。
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'admin_read'

    def get(self, request):
        return success({'csrfToken': get_token(request)}, message='CSRF token 已下发')


class ContactListCreateView(generics.ListCreateAPIView):
    """
    咨询留言集合接口。

    同一个路径承担两种语义，按请求方法区分权限：

      POST /api/contacts/   提交留言 —— 公开，任何访客都可提交
      GET  /api/contacts/   查看列表 —— 仅管理员

    提交时开启独立限流，防止脚本刷单；
    读取时使用管理员档位的限流。
    """

    queryset = Contact.objects.all()
    throttle_scope = 'contact_submit'

    # 本视图只开放查询与提交两种方法。
    # 显式列出后，DRF 对 PUT/DELETE 会直接返回 405，而不是落到
    # http_method_not_allowed 之前的认证环节。
    http_method_names = ['get', 'post', 'head', 'options']

    def get_serializer_class(self):
        # 提交用只读 status 的序列化器，读取用完整序列化器
        if self.request.method == 'POST':
            return ContactCreateSerializer
        return ContactSerializer

    def get_permissions(self):
        # 读取留言属于敏感操作，必须管理员登录；提交则是公开的
        if self.request.method == 'GET':
            return [IsAdminUser()]
        return [AllowAny()]

    def get_authenticators(self):
        # 提交是公开接口，但依然要校验 CSRF，因此沿用带 CSRF 的认证类
        if self.request.method.lower() not in self.http_method_names:
            # 不支持的方法（如 PUT）先不挂认证器，
            # 否则会被 CSRF 校验先拦下，返回误导性的 403 而不是更准确的 405
            return []
        return [CsrfEnforcedSessionAuthentication()]

    def get_throttles(self):
        # 提交与读取用不同的限流档位。
        # 注意：ScopedRateThrottle 每次都从视图的 `throttle_scope` 属性取值，
        # 所以必须改属性本身，改 `self.scope` 会被覆盖。
        self.throttle_scope = 'admin_read' if self.request.method == 'GET' else 'contact_submit'
        return super().get_throttles()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # 父类返回的是分页字典，这里再套一层统一信封
        return success(
            data=response.data,
            message='留言列表',
            code='ok',
            http_status=response.status_code,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.save()

        return success(
            data=ContactSerializer(contact).data,
            message='反馈已提交，感谢你的建议。',
            code='created',
            http_status=status.HTTP_201_CREATED,
        )


class ContactDetailView(generics.RetrieveUpdateAPIView):
    """查看 / 更新单条留言 —— 仅管理员。"""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAdminUser]
    authentication_classes = [SessionAuthentication]
    throttle_scope = 'admin_read'

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return success(
            data=response.data,
            message='留言详情',
            code='ok',
            http_status=response.status_code,
        )

    def update(self, request, *args, **kwargs):
        # partial_update 内部也会走到这里，PATCH 与 PUT 一并覆盖
        response = super().update(request, *args, **kwargs)
        return success(
            data=response.data,
            message='留言已更新',
            code='updated',
            http_status=response.status_code,
        )


# ---------------------------------------------------------------------------
# 早期示例接口，保留以便对照
# ---------------------------------------------------------------------------

def api_hello(request):
    """供前端调用的示例接口。"""
    return JsonResponse({
        'message': 'Hello from Django API!',
        'status': 'ok',
    })
