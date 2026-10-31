# design-codegen — django 侧契约消费形状（T-1 定稿，REQ-2026-028）

> 2026-10-31 人裁定稿：**方案 B —— manifest + datamodel-code-generator DTO 生成**。
> 先例依据：go 人裁原则（有主流生成器就不自研，2026-10-26）用于 DTO 层；
> openapi-generator 无 Django/DRF server 生成器（rails/laravel 同处境，ADR-0050 先例）
> → 路由面走自研 manifest 轻轮子（rails/laravel 两仓验证过的形状）。

## 1. 管线（gen-shared.sh 三步）

```
bash scripts/gen-shared.sh
  ① shared 仓 emit:openapi          （TypeSpec SSOT 单 emit，不落 shared 仓改动）
  ② datamodel-code-generator        （openapi.yaml → src/saas_identity_platform_django/contract/models/）
  ③ scripts/gen-manifest.py         （openapi.yaml → generated/api_manifest.json）
```

## 2. 生成区 / 手写区

| 区 | 路径 | 纪律 |
|---|---|---|
| 生成区（DTO） | `src/saas_identity_platform_django/contract/models/` | 禁手改；regen 先删后写 |
| 生成区（manifest） | `generated/api_manifest.json` | 禁手改；确定性产物（键序固定 + [tag,operationId] 排序 + 无时间戳 + LF） |
| 手写区 | `src/.../serializers.py` `views.py` `urls.py` `apps.py` `admin.py` | 实现缝；serializer 从生成 DTO 变换，路由对 manifest 校验 |

## 3. 强制面

- **route-parity 契约测试**（rails `route_parity_test.rb` 同构）：读 `generated/api_manifest.json`，
  断言 urls.py 路由表与 manifest 一致——缺端点红 / 私端点红（§4「API 面只认生成物」的落法）。
- **L4.codegen.idempotent 接线**：`scripts/checks/check_codegen_idempotent.py` 需加 django 识别分支
  （marker：gen-shared.sh 含 datamodel-code-generator + gen-manifest.py 字样；fastapi/flutter/harmonyos
  分支同构）。接线批任务，不落本批文档步。
- **版本钉位**：datamodel-code-generator 在 pyproject dev 组钉 exact（spike 首跑回填具体版本号），
  另记 version-lock.json；升级单独立项 ADR。
- **漂移 fail-loud**：生成区对 git HEAD 不一致（含 untracked）即红（fastapi 同款，防漏 commit 假绿）。

## 4. 切片落点（REQ-2026-028）

| 子项 | op | 端点 | DTO |
|---|---|---|---|
| I01 租户列表 | `AdminTenants_listTenants` | `GET /api/v1/admin/tenants` | 内联分页 wrapper `{items: Tenant[], page, pageSize, total}` |
| I02 创建租户 | `AdminTenants_createTenant` | `POST /api/v1/admin/tenants` | req `CreateTenantRequest{tenantKey, name}` → resp `Tenant` |
| I03 租户详情 | `AdminTenants_getTenant` | `GET /api/v1/admin/tenants/{id}` | resp `Tenant` |

分页语义：saas 家族 **0 基**分页（家族契约分页语义分叉在案——saas 0 基 / lab 不切片），
serializer 落法按契约 wrapper 字段直通，不自创分页参数。

## 5. 边界

- 实体层（DB-First 链）不在本定稿范围——django migrations vs 家族 DB-First 的张力随 T-2（models+migration）
  单独定，届时照家族六链先例（scaffold-models.mjs 系）评估。
- 手写 serializer 不允许出现 manifest 里没有的路由；反过来 manifest 有而 urls.py 没挂载的端点，
  parity 测试红。
