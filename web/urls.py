from django.urls import path

from . import api, views

app_name = 'web'

urlpatterns = [
    # ---------------- 后端接口 ----------------
    path('api/', api.ApiIndexView.as_view(), name='api_index'),
    path('api/hello/', api.api_hello, name='api_hello'),
    path('api/csrf/', api.CsrfTokenView.as_view(), name='api_csrf'),
    # 咨询留言：POST 公开提交 / GET 需管理员
    path('api/contacts/', api.ContactListCreateView.as_view(), name='api_contacts'),
    # 查看 / 更新单条留言（仅管理员）
    path('api/contacts/<int:pk>/', api.ContactDetailView.as_view(), name='api_contact_detail'),

    # ---------------- 官网五个根页面 ----------------
    # 各自对应一份独立的 HTML 文档
    path('', views.page, {'name': 'index'}, name='home'),
    path('product/', views.page, {'name': 'product'}, name='product'),
    path('factory/', views.page, {'name': 'factory'}, name='factory'),
    path('custom/', views.page, {'name': 'custom'}, name='custom'),
    path('contact/', views.page, {'name': 'contact'}, name='contact'),
]
