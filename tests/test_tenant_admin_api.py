"""M00.F01 租户维护首切片（REQ-2026-028，T-4）——I01/I02/I03 行为单测。

契约 SSOT：shared emit openapi（docs/design/design-codegen.md）。
鉴权语义：CT 仲裁 admin-tenants.test.ts——dev 模式 /admin/** authenticated 即可，
缺失/无效凭证 401（AC-5）；角色 403 不在本切片（AC-6 澄清修正）。
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

LIST_URL = "/api/v1/admin/tenants"
ALICE_ID = uuid.UUID("00000000-0000-0000-0000-b00000000001")
TENANT_FIELDS = {"id", "tenantKey", "name", "status", "createdAt", "updatedAt"}


def principal() -> SimpleNamespace:
    """force_authenticate 最小主体（属性面与 auth.Principal 对齐）。"""
    return SimpleNamespace(is_authenticated=True, id=ALICE_ID, tenant_id=None)


def client() -> APIClient:
    c = APIClient()
    c.force_authenticate(user=principal())
    return c


# ---------- I01 租户列表 ----------


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I01")
def test_list_unauthenticated_401() -> None:
    resp = APIClient().get(LIST_URL)
    assert resp.status_code == 401


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I01")
def test_list_invalid_token_401() -> None:
    resp = APIClient().get(LIST_URL, HTTP_AUTHORIZATION="Bearer not-a-jwt")
    assert resp.status_code == 401


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I01")
def test_list_200_wrapper_zero_based() -> None:
    from tenants.models import Tenant

    resp = client().get(LIST_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"items", "page", "pageSize", "total"}
    assert body["page"] == 0  # saas 家族 0 基（Spring Data Pageable 语义）
    assert body["pageSize"] == 20
    assert body["total"] == Tenant.objects.count()
    created = [it["createdAt"] for it in body["items"]]
    assert created == sorted(created, reverse=True)  # created_at DESC
    first = body["items"][0]
    assert set(first) == TENANT_FIELDS
    assert first["status"] in ("active", "suspended")


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I01")
def test_list_page_size_explicit() -> None:
    resp = client().get(LIST_URL, {"page": "1", "pageSize": "2"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["pageSize"] == 2
    assert len(body["items"]) <= 2


# ---------- I02 创建租户 ----------


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I02")
def test_create_unauthenticated_401() -> None:
    resp = APIClient().post(LIST_URL, {"tenantKey": "x", "name": "x"}, format="json")
    assert resp.status_code == 401


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I02")
def test_create_200_active_with_family_side_effects() -> None:
    from tenants.models import Tenant, TenantApplication, TenantMember

    payload = {"tenantKey": "dj-slice-t1", "name": "Django 切片租户"}
    resp = client().post(LIST_URL, payload, format="json")
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert set(body) == TENANT_FIELDS
    assert body["tenantKey"] == "dj-slice-t1"
    assert body["status"] == "active"  # 契约缺省 active；DB smallint 1
    row = Tenant.objects.get(tenant_key="dj-slice-t1")
    assert row.status == 1
    # 家族副作用（2026-09-12 用户裁定）：建租户者入成员表 + 默认订阅 lab-management
    assert TenantMember.objects.filter(tenant_id=row.id, user_id=ALICE_ID, status=1).exists()
    assert TenantApplication.objects.filter(
        tenant_id=row.id, client_id="lab-management", status=1
    ).exists()


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I02")
def test_create_conflict_409() -> None:
    c = client()
    payload = {"tenantKey": "dj-slice-dup", "name": "重复键租户"}
    assert c.post(LIST_URL, payload, format="json").status_code == 200
    resp = c.post(LIST_URL, payload, format="json")
    assert resp.status_code == 409
    assert resp.json()["code"] == "CONFLICT"


# ---------- I03 租户详情 ----------


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I03")
def test_detail_200_seed_row() -> None:
    from tenants.models import Tenant

    seed = Tenant.objects.order_by("created_at").first()
    assert seed is not None
    resp = client().get(f"{LIST_URL}/{seed.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == TENANT_FIELDS
    assert body["id"] == str(seed.id)
    assert body["tenantKey"] == seed.tenant_key


@pytest.mark.django_db
@pytest.mark.fn("M00.F01.I03")
def test_detail_404_unknown_id() -> None:
    resp = client().get(f"{LIST_URL}/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
