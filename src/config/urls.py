"""URL 路由 —— 身份平台 Django 版（saas-identity-platform-django）。

按 shared 契约生成物挂载端点（suite-hard-rules §4，禁止手写与契约漂移的路由）；
tests/test_route_parity.py 双向守卫（缺端点红 + 私端点红）。
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", include("tenants.urls")),
]
