"""租户域模型——DB-First（family schema 归 drizzle SSOT，全 managed=False 消费）。

不产 django 迁移：表由家族迁移链（drizzle）拥有，django 只读写。
pk/时间戳用 db_default 走 PG 侧默认（uuid_generate_v4 / CURRENT_TIMESTAMP），
ORM INSERT 不携带这些列；列形以 drizzle schema（nextjs 仓 src/db/schema.ts）为准。
"""

from __future__ import annotations

from django.db import models
from django.db.models import Func


class UuidV4(Func):
    function = "uuid_generate_v4"


class CurrentTimestamp(Func):
    function = "CURRENT_TIMESTAMP"


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UuidV4())
    tenant_key = models.CharField(max_length=64, unique=True, db_column="tenant_key")
    name = models.CharField(max_length=128)
    status = models.SmallIntegerField()  # 1=active 2=suspended
    created_at = models.DateTimeField(db_column="created_at", db_default=CurrentTimestamp())
    updated_at = models.DateTimeField(db_column="updated_at", db_default=CurrentTimestamp())

    class Meta:
        managed = False
        db_table = "tenant"

    def __str__(self) -> str:
        return f"{self.tenant_key}({self.name})"


class TenantMember(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UuidV4())
    tenant_id = models.UUIDField()
    user_id = models.UUIDField()
    # member_name 列在 drizzle schema 就是 nullable，如实映射
    member_name = models.CharField(max_length=64, blank=True, null=True)  # noqa: DJ001
    is_owner = models.BooleanField(default=False)
    status = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField(db_default=CurrentTimestamp())
    updated_at = models.DateTimeField(db_default=CurrentTimestamp())

    class Meta:
        managed = False
        db_table = "tenant_member"

    def __str__(self) -> str:
        return f"member(tenant={self.tenant_id}, user={self.user_id})"


class TenantApplication(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UuidV4())
    tenant_id = models.UUIDField()
    client_id = models.CharField(max_length=64, db_column="client_id")
    status = models.SmallIntegerField(default=1)
    expire_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=CurrentTimestamp())

    class Meta:
        managed = False
        db_table = "tenant_application"

    def __str__(self) -> str:
        return f"app(tenant={self.tenant_id}, client={self.client_id})"


class OAuthClient(models.Model):
    id = models.UUIDField(primary_key=True, db_default=UuidV4())
    client_id = models.CharField(max_length=64, db_column="client_id")

    class Meta:
        managed = False
        db_table = "oauth_client"

    def __str__(self) -> str:
        return str(self.client_id)
