# REQ-2026-028 saas-django 租户管理首切片（M00.F01 列表/创建/详情）

| 项 | 值 |
|---|---|
| 提出人 | 用户 |
| 提出日期 | 2026-10-31 |
| 优先级 | P1 |
| 状态 | 已评审 |
| 关联 ADR | — |

## 1. 需求描述

> **用户原话**：「saas：租户管理首切片」（选项描述：M00 租户 CRUD 最小切片——列表/创建/详情，照其他栈首切片先例）。

**我的理解**：saas-identity-platform-django 的第一个业务 REQ——`M00.F01 租户维护` 的最小切片，覆盖 shared 契约 `/admin/tenants` 三个操作：列表（I01）/ 创建（I02）/ 详情（I03）。更新（I04）/ 删除（I05）不在本 REQ 范围，随后续切片进来。API 面只认 shared 契约生成物（§4），路径与 DTO 以 `admin-tenants.tsp` 生成物为准。

### 澄清记录

| 疑问 | 澄清结论 | 澄清人 | 日期 |
|---|---|---|---|
| 首切片范围只含 I01/I02/I03？ | 是——列表/创建/详情三面；I04/I05 随后续切片 | 用户（范围选项确认） | 2026-10-31 |
| REQ 编号 028 从哪来？ | 家族主系列顺延（最高 REQ-2026-027=angular 骨架，同日）；100 系是 lab-e2e 内部系列 | Claude 推断，留人核 | 2026-10-31 |
| AC 表路径无 `/api/v1` 前缀？ | 功能树端点注记是简写；契约 SSOT 实际路径带 `/api/v1` 前缀（`GET/POST /api/v1/admin/tenants` 等），实现与测试按契约 | Claude 核契约时确认 | 2026-10-31 |
| AC-2 原写 201，契约实际返回码？ | 契约 SSOT `POST /api/v1/admin/tenants` responses 只有 `200`（无 201）——AC-2 已改为 200 | Claude 核 openapi.yaml 时确认 | 2026-10-31 |
| AC-6 原写 403，非 platform_admin 真的 403？ | 否——contract-test/tests/admin-tenants.test.ts L3 裁定：dev 模式 `/admin/**` 对四栈统一是「authenticated 即可」（401 无效凭证；springboot 的 platform_admin scope 是 prod 注释，DB 无该角色列）。AC-6 已改为同 CT 仲裁 | Claude 查 CT 仲裁时确认 | 2026-10-31 |
| T-5 要在 contract-test 加什么断言？ | 零断言变更——本切片端点面与 shared 契约零出入（契约早已存在），CT I29/I30/I31/I60 已覆盖三 op 断言。django 不进 `TARGETS`：CT 治理「声明即必须可达」，本切片无 update/delete，注册后 I32/I33 立红；照 ktor/laravel 先例——**TARGETS 注册随 update/delete 切片落地** | Claude 查 CT 治理与先例时确认，留人核 | 2026-10-31 |

## 2. 验收标准

| 编号 | 场景（给定） | 操作（当） | 预期（则） |
|---|---|---|---|
| AC-1 | 平台库已有若干租户，platform_admin 已认证 | `GET /admin/tenants`（分页参数） | 200 + shared 契约分页 DTO 形状 |
| AC-2 | 已认证，payload 合法 | `POST /admin/tenants` | 200 + 详情形状（契约 responses 只认 200）；tenant_key 冲突 409；status 缺省 active |
| AC-3 | platform_admin 已认证，ID 存在 | `GET /admin/tenants/{id}` | 200 详情形状（状态/到期时间/订阅应用数） |
| AC-4 | 租户 ID 不存在 | `GET /admin/tenants/{id}` | 404，无兜底 |
| AC-5 | 未认证 | 任一端点 | 401（§3 业务身份字段缺失禁止兜底） |
| AC-6 | 已认证（任意角色） | 任一端点 | 放行（CT 仲裁：dev 模式 authenticated 即可；本切片不实现 403 角色检查） |
| AC-7 | 三个端点全落地 | — | contract-test 仓同步断言（§2 硬规则） |

## 3. 任务拆解

| 任务 ID | 任务描述 | 类型 | 负责人 | 预估 | 状态 |
|---|---|---|---|---|---|
| T-1 | 契约消费形状定稿——django 侧 shared 生成物管线 Phase 1 未接，先定 TypeSpec→DRF serializers/urls 生成路径 | 设计 | 待定 | 0.5d | 已完成（2026-10-31 人裁方案 B，见 docs/design/design-codegen.md） |
| T-2 | models + migration（tenant / sys_user / tenant_member / tenant_application 关系面） | 开发 | 待定 | 1d | 已完成（2026-10-31；DB-First 裁定：family 表归 drizzle SSOT，`managed=False` 免迁移，无 django 建表） |
| T-3 | serializers + views + urls（三 op，显式 serializer_class/queryset，权限 platform_admin） | 开发 | 待定 | 1d | 已完成（2026-10-31；鉴权按 CT 仲裁=authenticated 即可，无 403 角色检查——见澄清记录 AC-6） |
| T-4 | 测试挂 `@pytest.mark.fn`（I01/I02/I03，覆盖 AC-1..7） | 开发 | 待定 | 0.5d | 已完成（2026-10-31；红灯 10 失败在案 → 实现 → 14 passed 全绿；含路由 parity 双向守卫） |
| T-5 | contract-test 仓同步断言（§2 硬规则） | 开发 | 待定 | 0.5d | 已完成（重定性 2026-10-31：端点面零变更 → 零断言变更；django 不进 CT TARGETS，随 update/delete 切片注册——ktor/laravel 先例，见澄清记录） |

## 4. 功能影响（需求与功能对齐的唯一位置）

> ID 均已在 `docs/functions/function-tree.md`；I01-I03 为本 REQ 提案内 mirror 登记（令牌已焚）。

| 功能 ID | 功能名称 | 影响类型 | 说明 | 关联任务 |
|---|---|---|---|---|
| M00.F01 | 租户维护 | 变更 | 首切片实现 3/5 子项 | T-1..T-5 |
| M00.F01.I01 | 租户列表 | 新增（登记） | 镜像登记，状态=规划 | T-1..T-5 |
| M00.F01.I02 | 创建租户 | 新增（登记） | 镜像登记，状态=规划 | T-1..T-5 |
| M00.F01.I03 | 租户详情 | 新增（登记） | 镜像登记，状态=规划 | T-1..T-5 |

## 5. 流程影响

无——本仓尚无 flow-function-map（首个流程随首切片建立）。

## 6. 风险与回滚

| 风险 | 影响面 | 缓解 | 回滚方式 |
|---|---|---|---|
| codegen 未接线——django 侧 shared 生成物管线 Phase 1 未落（§4 只认生成物） | T-3 端点形状 | T-1 先行定稿生成路径，人不点头不开工 | — |
| DB/seed 接线首跑（DATABASE_URL 指 saas_dev，migrate 首次执行） | T-2 | .env.local 真值人核 | 迁移可逆（migrate <zero>） |
| contract-test 同步纪律（§2） | T-5 | 同 commit 同步断言 | — |

---

I 级登记已于本 REQ 提案内完成（mirror 免批，令牌已焚；sync_files 本文档已同步落盘）。
