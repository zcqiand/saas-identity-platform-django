"""租户管理三端点（M00.F01 I01/I02/I03）——语义对齐 nextjs 参考实现（跨栈一致）。

- list：page 0 基缺省 0、pageSize 缺省 20 上限 100、created_at DESC（saas 分页语义），
  响应 wrapper {items, page, pageSize, total}（契约 inline 形状）——分页内联在 list()，
  不子类化 BasePagination（其 paginate_queryset 签名是方法级 TypeVar，具体化即 Liskov 红）
- create：200（契约 responses 只认 200）；tenant_key 平台唯一，冲突 409 CONFLICT；
  副作用=建租户者入 tenant_member + 默认订阅 lab-management（2026-09-12 用户裁定）
- detail：未知 id 404 NOT_FOUND；错误体 {code, message}（契约 ErrorResponse 形状）
"""

from __future__ import annotations

import uuid
from typing import cast

from django.db import IntegrityError, transaction
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import OAuthClient, Tenant, TenantApplication, TenantMember
from tenants.serializers import STATUS_TO_SMALLINT, TenantCreateSerializer, TenantSerializer

DEFAULT_TENANT_APP = "lab-management"


def _parse_page_param(raw: str | None, default: int) -> int:
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


class TenantListCreateView(generics.ListCreateAPIView[Tenant]):
    queryset = Tenant.objects.order_by("-created_at")
    serializer_class = TenantSerializer

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        queryset = self.get_queryset().order_by("-created_at")
        page = _parse_page_param(request.query_params.get("page"), 0)  # saas 0 基
        page_size = _parse_page_param(request.query_params.get("pageSize"), 20)
        page_size = max(1, min(page_size, 100))
        total = queryset.count()
        items = list(queryset[page * page_size : (page + 1) * page_size])
        data = [TenantSerializer(t).data for t in items]
        return Response({"items": data, "page": page, "pageSize": page_size, "total": total})

    def create(  # noqa: ARG002 (DRF 分发签名，args/kwargs 由 ruff variadic 豁免)
        self, request: Request, *args: object, **kwargs: object
    ) -> Response:
        in_ser = TenantCreateSerializer(data=request.data)
        in_ser.is_valid(raise_exception=True)
        data = in_ser.validated_data
        # Bearer 层（saas_identity_platform_django.auth）保证 authenticated 时
        # request.user 是 Principal（id=uuid）；force_authenticate 测试主体同属性面
        user_id = cast(uuid.UUID, request.user.id)
        try:
            with transaction.atomic():
                tenant = Tenant.objects.create(
                    tenant_key=data["tenant_key"],
                    name=data["name"],
                    status=STATUS_TO_SMALLINT["active"],
                )
                # 家族副作用（2026-09-12 用户裁定）：建租户者入成员表 + 默认订阅
                TenantMember.objects.create(tenant_id=tenant.id, user_id=user_id, status=1)
                if OAuthClient.objects.filter(client_id=DEFAULT_TENANT_APP).exists():
                    TenantApplication.objects.create(
                        tenant_id=tenant.id, client_id=DEFAULT_TENANT_APP, status=1
                    )
        except IntegrityError:
            return Response(
                {"code": "CONFLICT", "message": "Tenant key already exists"}, status=409
            )
        return Response(TenantSerializer(tenant).data, status=200)


class TenantDetailView(APIView):
    def get(self, _request: Request, tenant_id: uuid.UUID) -> Response:
        tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            return Response({"code": "NOT_FOUND", "message": "Tenant not found"}, status=404)
        return Response(TenantSerializer(tenant).data, status=200)
