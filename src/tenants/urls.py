"""租户域路由——挂载点 config/urls.py 的 api/v1/ 前缀下；路径以契约 manifest 为准
（tests/test_route_parity.py 双向守卫：缺端点红 + 私端点红）。"""

from __future__ import annotations

from django.urls import URLPattern, path

from tenants.views import TenantDetailView, TenantListCreateView

app_name = "tenants"

urlpatterns: list[URLPattern] = [
    path("admin/tenants", TenantListCreateView.as_view()),
    path("admin/tenants/<uuid:tenant_id>", TenantDetailView.as_view()),
]
