# React + Redux 前端重构方案

## 1. 概述

### 1.1 重构目标

将现有的单文件 HTML 模板重构为 React + Redux 架构，实现：

- **组件化开发** - 可复用的 UI 组件
- **状态管理** - Redux 统一管理应用状态
- **类型安全** - TypeScript 支持
- **现代化构建** - Vite 快速开发与构建
- **可测试性** - 组件和 Redux 逻辑可独立测试

### 1.2 技术栈

| 技术 | 用途 |
|------|------|
| React 18 | UI 框架 |
| Redux Toolkit | 状态管理 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| TailwindCSS | 样式框架 |
| React Router | 路由管理 |
| Vitest | 单元测试 |
| React Testing Library | 组件测试 |

### 1.3 部署方式

采用「前端打包嵌入后端」方式：

```
backend/static/dist/    # React 构建产物
├── index.html
├── assets/
│   ├── index-xxx.js
│   └── index-xxx.css
└── ...
```

FastAPI 直接托管静态文件，无需额外的前端服务器。

## 2. 项目结构

```
user-intent-mcp/
├── src/                      # Python 后端 (保持不变)
│   ├── core.py
│   ├── web_multi_tenant.py
│   └── ...
│
├── frontend/                 # React 前端 (新增)
│   ├── src/
│   │   ├── main.tsx          # 入口
│   │   ├── App.tsx           # 根组件
│   │   ├── routes.tsx        # 路由配置
│   │   │
│   │   ├── components/       # 通用组件
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   ├── Input/
│   │   │   └── Layout/
│   │   │
│   │   ├── features/         # 功能模块 (Redux Slice)
│   │   │   ├── auth/
│   │   │   │   ├── authSlice.ts
│   │   │   │   ├── AuthPage.tsx
│   │   │   │   └── components/
│   │   │   ├── tasks/
│   │   │   │   ├── tasksSlice.ts
│   │   │   │   ├── TasksPage.tsx
│   │   │   │   └── components/
│   │   │   ├── admin/
│   │   │   │   ├── adminSlice.ts
│   │   │   │   ├── AdminPage.tsx
│   │   │   │   └── components/
│   │   │   └── user/
│   │   │       ├── userSlice.ts
│   │   │       ├── UserPage.tsx
│   │   │       └── components/
│   │   │
│   │   ├── hooks/            # 自定义 Hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useApiKey.ts
│   │   │   └── usePolling.ts
│   │   │
│   │   ├── services/         # API 服务
│   │   │   ├── api.ts        # Axios 实例
│   │   │   ├── authApi.ts
│   │   │   ├── tasksApi.ts
│   │   │   └── userApi.ts
│   │   │
│   │   ├── store/            # Redux Store
│   │   │   ├── index.ts
│   │   │   └── middleware/
│   │   │
│   │   ├── types/            # TypeScript 类型
│   │   │   ├── auth.ts
│   │   │   ├── task.ts
│   │   │   └── user.ts
│   │   │
│   │   └── utils/            # 工具函数
│   │       ├── storage.ts
│   │       └── formatters.ts
│   │
│   ├── tests/                # 测试文件
│   │   ├── components/
│   │   ├── features/
│   │   └── utils/
│   │
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── scripts/                  # 构建脚本
│   └── build-frontend.sh
│
└── docs/
    ├── REFACTOR-react-redux.md  # 本文档
    ├── DEV-PLAN.md              # 开发计划
    └── TEST-PLAN.md             # 测试计划
```

## 3. Redux 架构设计

### 3.1 Store 结构

```typescript
interface RootState {
  auth: AuthState;
  tasks: TasksState;
  user: UserState;
  admin: AdminState;
  ui: UIState;
}
```

### 3.2 Auth Slice

```typescript
// features/auth/authSlice.ts
interface AuthState {
  apiKey: string | null;
  apiKeyExpiry: number | null;
  isAuthenticated: boolean;
  loginStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setApiKey: (state, action: PayloadAction<string>) => {},
    clearApiKey: (state) => {},
    loadCachedAuth: (state) => {},
  },
});
```

### 3.3 Tasks Slice

```typescript
// features/tasks/tasksSlice.ts
interface TasksState {
  pending: Task[];
  history: Task[];
  selectedTaskId: string | null;
  pollingStatus: 'idle' | 'polling' | 'paused';
}

interface Task {
  id: string;
  question: string;
  status: 'PENDING' | 'COMPLETED' | 'DISMISSED';
  answer?: string;
  image?: string;
  createdAt: string;
  completedAt?: string;
}
```

### 3.4 User Slice

```typescript
// features/user/userSlice.ts
interface UserState {
  profile: UserProfile | null;
  feishuNotifyEnabled: boolean;
  loadingStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
}

interface UserProfile {
  name: string;
  avatarUrl?: string;
  email?: string;
  isActive: boolean;
}
```

## 4. 页面映射

| 原 HTML 模板 | React 页面 | 路由 |
|-------------|-----------|------|
| `multi_tenant.html` (初始化) | `InitPage` | `/init` |
| `multi_tenant.html` (登录) | `LoginPage` | `/login` |
| `multi_tenant.html` (管理后台) | `AdminPage` | `/admin` |
| `multi_tenant.html` (用户中心) | `UserPage` | `/user` |
| `index.html` (WebUI) | `TasksPage` | `/` |

## 5. API 服务层

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/',
});

// 请求拦截器 - 添加 Authorization Header
api.interceptors.request.use((config) => {
  const apiKey = store.getState().auth.apiKey;
  if (apiKey) {
    config.headers.Authorization = `Bearer ${apiKey}`;
  }
  return config;
});

export default api;
```

## 6. 构建与部署

### 6.1 开发模式

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
# API 代理到后端 http://localhost:8000
```

### 6.2 构建生产版本

```bash
cd frontend
npm run build
# 产物输出到 frontend/dist/
```

### 6.3 嵌入后端

```bash
./scripts/build-frontend.sh
# 1. 构建前端
# 2. 复制到 src/static/dist/
# 3. 后端自动托管
```

### 6.4 后端配置

```python
# web_multi_tenant.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# API 路由 (优先级高)
# ...

# 前端静态文件 (最后挂载)
app.mount("/", StaticFiles(directory="static/dist", html=True), name="frontend")
```

## 7. 迁移策略

### 阶段 1: 基础设施 (1-2天)
- 创建 React 项目
- 配置 Vite + TypeScript
- 配置 TailwindCSS
- 设置 Redux Store

### 阶段 2: 认证模块 (1-2天)
- 实现 AuthSlice
- 迁移登录页面
- 迁移缓存登录
- 迁移飞书 OAuth

### 阶段 3: 任务模块 (2-3天)
- 实现 TasksSlice
- 迁移任务列表
- 迁移任务详情
- 迁移回复功能
- 迁移历史记录

### 阶段 4: 用户模块 (1天)
- 实现 UserSlice
- 迁移用户中心
- 迁移飞书通知设置

### 阶段 5: 管理后台 (1-2天)
- 实现 AdminSlice
- 迁移系统配置
- 迁移用户管理

### 阶段 6: 测试与优化 (1-2天)
- 编写单元测试
- 编写集成测试
- 性能优化
- 文档完善

## 8. 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| 开发周期长 | 分阶段交付，每阶段可独立部署 |
| 功能遗漏 | 对照原 HTML 逐功能核对 |
| 样式不一致 | 使用 TailwindCSS 保持设计语言 |
| API 变更 | 先完成后端 API 重构，再开发前端 |
