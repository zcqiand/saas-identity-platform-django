"""serializer 从生成 DTO 变换（design-codegen.md 方案 B：contract DTO 区为形状真源）。

status 走 smallint <-> TenantStatus 枚举映射（DB 1=active 2=suspended，契约字符串）。
"""

from __future__ import annotations

from rest_framework import serializers

from tenants.models import Tenant

STATUS_TO_SMALLINT: dict[str, int] = {"active": 1, "suspended": 2}


def status_from_smallint(status: int) -> str:
    """家族语义（nextjs 参考实现同款）：仅 2=suspended，其余一律 active。"""
    return "suspended" if status == 2 else "active"


class TenantSerializer(serializers.Serializer[Tenant]):
    """契约 Tenant DTO（id/tenantKey/name/status/createdAt/updatedAt）。"""

    id = serializers.UUIDField(read_only=True)
    tenantKey = serializers.CharField(source="tenant_key", read_only=True)  # noqa: N815
    name = serializers.CharField(read_only=True)
    status = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)  # noqa: N815
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)  # noqa: N815

    def get_status(self, obj: Tenant) -> str:
        return status_from_smallint(obj.status)


class TenantCreateSerializer(serializers.Serializer[dict[str, str]]):
    """契约 CreateTenantRequest（required: tenantKey/name——「绑定初始管理员」不在契约面）。"""

    tenantKey = serializers.CharField(source="tenant_key", max_length=64)  # noqa: N815
    name = serializers.CharField(max_length=128)
