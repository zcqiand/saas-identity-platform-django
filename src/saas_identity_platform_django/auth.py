"""Bearer JWT 鉴权（HS256）——家族镜像约定（nextjs src/lib/jwt.ts 同款形状）。

- Authorization: Bearer <jwt>；缺失/无效/过期 -> None -> DRF 401（AC-5，无兜底）
- claims：sub = user id（建租户副作用写 tenant_member 的权威源）、tenant_id 为
  path :tenantId 比对的权威源（本切片 /admin/** 未用）、iss/aud/exp 由 PyJWT 校验
- 角色不在这里判——CT 仲裁 admin-tenants.test.ts：dev 模式 authenticated 即可（AC-6）
"""

from __future__ import annotations

import uuid

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request


class Principal:
    """最小请求主体——非 django User（family 库无 django 表）；属性面对齐 view 消费。"""

    is_authenticated = True

    def __init__(self, user_id: uuid.UUID, tenant_id: uuid.UUID | None) -> None:
        self.id = user_id
        self.tenant_id = tenant_id


class BearerAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[Principal, None] | None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        token = header[len("Bearer ") :]
        try:
            claims = jwt.decode(
                token,
                settings.JWT_SIGNING_KEY,
                algorithms=["HS256"],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
            )
        except jwt.PyJWTError:
            return None  # 无效凭证 -> 401（NotAuthenticated），不暴露失败原因
        user_id = claims.get("sub")
        if not isinstance(user_id, str):
            return None
        tenant_raw = claims.get("tenant_id")
        try:
            tenant_id = uuid.UUID(tenant_raw) if tenant_raw else None
            return Principal(uuid.UUID(user_id), tenant_id), None
        except (ValueError, TypeError):
            return None

    def authenticate_header(self, _request: Request) -> str:
        return "Bearer"
