# 项目文档

本目录包含 User Intent MCP 项目的设计与开发文档。

## 版本规划

| 版本 | 阶段 | 状态 | 说明 |
|------|------|------|------|
| v0.1.0 | 多租户模式 | ✅ 已完成 | 飞书登录、消息隔离、Web UI |
| v0.9.0 | React 前端 | 🚧 开发中 | React + Redux 前后端分离 |
| v1.0.0 | 正式发布 | 📋 计划中 | 功能完善、生产就绪 |

---

## v0.1.0 - 多租户模式

**目录**: `v0.1.0-multi-tenant/`

| 文档 | 说明 |
|------|------|
| [PRD-feishu-multi-tenant.md](v0.1.0-multi-tenant/PRD-feishu-multi-tenant.md) | 产品需求文档 |
| [DESIGN-feishu-multi-tenant.md](v0.1.0-multi-tenant/DESIGN-feishu-multi-tenant.md) | 技术设计文档 |
| [diagrams/](v0.1.0-multi-tenant/diagrams/) | 架构图、流程图 |

### 主要功能

- 飞书 OAuth 登录
- 多用户消息隔离
- 30 天登录缓存
- Authorization Header 认证
- 管理后台

### 技术栈

- Python 3.12+
- FastAPI
- FastMCP
- SQLite
- 原生 HTML/CSS/JS

---

## v0.9.0 - React 前端

**目录**: `v0.9.0-react-frontend/`

| 文档 | 说明 |
|------|------|
| [REFACTOR-react-redux.md](v0.9.0-react-frontend/REFACTOR-react-redux.md) | 重构方案设计 |
| [DEV-PLAN.md](v0.9.0-react-frontend/DEV-PLAN.md) | 开发计划 |
| [TEST-PLAN.md](v0.9.0-react-frontend/TEST-PLAN.md) | TDD 测试计划 |

### 主要变更

- HTML 模板重构为 React 组件
- Redux Toolkit 状态管理
- TypeScript 类型安全
- Vite 构建工具
- TailwindCSS 样式
- Vitest 单元测试

### 技术栈

- React 18
- Redux Toolkit
- TypeScript
- Vite
- TailwindCSS
- React Router
- Vitest + React Testing Library

### 开发周期

预计 8-12 个工作日，分 6 个阶段：

1. 基础设施 (Day 1-2)
2. 认证模块 (Day 3-4)
3. 任务模块 (Day 5-7)
4. 用户模块 (Day 8)
5. 管理后台 (Day 9-10)
6. 测试优化 (Day 11-12)

---

## 后续版本规划

| 版本 | 功能 | 状态 |
|------|------|------|
| v0.9.1 | 深色/浅色主题切换 | 📋 计划中 |
| v0.9.2 | PWA 离线支持 | 📋 计划中 |
| v1.0.0 | 正式发布 | 📋 计划中 |
