# design-function-map — SaaS 多租户多应用身份平台 Django 版

> 人填、人评审。机器只检查功能 ID 存在性。
> 回答一个问题：**这个功能子项，落到哪段代码、哪张表、哪个权限码上？**
> 答不上来的行，说明设计没做完，别开工。

## 映射表

| 功能子项 ID | 页面/组件 | 接口 | 数据表 | 权限码 | 设计稿 | 状态 |
|---|---|---|---|---|---|---|
| M00.F01.I01 | admin 租户列表（本批仅后端接口） | `GET /api/v1/admin/tenants` | tenant | M00.F01.I01 | design-codegen.md | 开发中 |
| M00.F01.I02 | admin 创建租户（本批仅后端接口） | `POST /api/v1/admin/tenants` | tenant | M00.F01.I02 | design-codegen.md | 开发中 |
| M00.F01.I03 | admin 租户详情（本批仅后端接口） | `GET /api/v1/admin/tenants/{id}` | tenant | M00.F01.I03 | design-codegen.md | 开发中 |

## 约定

1. **权限码 = 功能子项 ID。** 权限判断直接写 ID；三个端点都要求 platform_admin。
2. 一个接口服务多个子项时，多行重复写。
3. 状态列必须与功能清单一致。不一致以功能清单为准。

## 评审时问这三个问题

1. 有没有子项没有权限码？→ 那它就是任何人都能点的按钮
2. 有没有一张表被三个以上模块直接写入？→ 边界破了（tenant 表本批只被 M00 写）
3. 「开发中」的行里接口和表填了吗？→ 没填就是还在纸上，别报进度

## 与 shared 树描述的出入（澄清）

shared 树 I02 描述「绑定初始管理员与默认配置」，但现行契约 `CreateTenantRequest`
只有 `tenantKey` + `name` 两字段——**契约是 SSOT**（admin-tenants.tsp 生成物为准），
本仓按契约实现；描述侧出入已记 REQ-2026-028 澄清记录。
