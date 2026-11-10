from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Vue 构建产物目录（由 `npm run build` 生成）
FRONTEND_DIR = Path(settings.BASE_DIR) / 'web' / 'static' / 'frontend'

# 五个根页面对应的 HTML 文件
PAGES = {
    'index': 'index.html',
    'product': 'product.html',
    'factory': 'factory.html',
    'custom': 'custom.html',
    'contact': 'contact.html',
}


def page(request, name):
    """
    返回指定根页面的 HTML。

    官网采用多页架构，五个导航项各自对应一个独立的 HTML 入口，
    而不是单页应用里的路由切换。
    """
    filename = PAGES.get(name)
    target = FRONTEND_DIR / filename if filename else None

    if target and target.exists():
        return HttpResponse(
            target.read_text(encoding='utf-8'),
            content_type='text/html',
        )

    # 尚未构建前端时给出明确提示，而不是抛 404
    return render(request, 'web/build_hint.html', status=200)


def api_hello(request):
    """供前端调用的示例接口。"""
    return JsonResponse({
        'message': 'Hello from Django API!',
        'status': 'ok',
    })
