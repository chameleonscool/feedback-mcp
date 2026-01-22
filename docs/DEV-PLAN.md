# React + Redux 前端开发计划

## 项目信息

| 项目 | 信息 |
|------|------|
| 项目名称 | User Intent MCP 前端重构 |
| 开发周期 | 8-12 个工作日 |
| 技术栈 | React 18 + Redux Toolkit + TypeScript + Vite |
| 分支 | `feishu-multi-tenant` |

## 开发阶段

### 阶段 1: 基础设施搭建 (Day 1-2)

#### 1.1 项目初始化

- [ ] 使用 Vite 创建 React + TypeScript 项目
- [ ] 配置 ESLint + Prettier
- [ ] 配置 TailwindCSS
- [ ] 配置路径别名 (`@/components`, `@/features` 等)

#### 1.2 Redux Store 配置

- [ ] 安装 Redux Toolkit
- [ ] 创建 Store 配置
- [ ] 配置 Redux DevTools
- [ ] 创建基础类型定义

#### 1.3 API 服务层

- [ ] 配置 Axios 实例
- [ ] 实现请求拦截器 (Authorization Header)
- [ ] 实现响应拦截器 (错误处理)
- [ ] 配置 Vite 代理 (开发环境)

#### 1.4 基础组件

- [ ] Button 组件
- [ ] Input 组件
- [ ] Card 组件
- [ ] Modal 组件
- [ ] Alert 组件
- [ ] Spinner 组件
- [ ] Layout 组件

**交付物：**
- 可运行的 React 项目
- 基础组件库
- Redux Store 框架

---

### 阶段 2: 认证模块 (Day 3-4)

#### 2.1 Auth Slice

- [ ] 定义 AuthState 类型
- [ ] 实现 authSlice
  - [ ] `setApiKey` - 设置 API Key
  - [ ] `clearApiKey` - 清除 API Key
  - [ ] `loadCachedAuth` - 加载缓存的认证信息
- [ ] 实现持久化 (localStorage)

#### 2.2 页面组件

- [ ] LoginPage - 登录页面
  - [ ] 飞书登录按钮
  - [ ] 管理员登录入口
  - [ ] 访客模式入口
- [ ] CachedLoginPage - 缓存登录页面
  - [ ] 欢迎回来界面
  - [ ] 继续使用按钮
  - [ ] 切换账号按钮
  - [ ] 退出登录按钮
- [ ] AdminLoginPage - 管理员登录页面
- [ ] InitPage - 初始化设置页面

#### 2.3 Hooks

- [ ] `useAuth` - 认证状态管理
- [ ] `useApiKey` - API Key 操作

#### 2.4 路由配置

- [ ] 配置 React Router
- [ ] 实现路由守卫 (认证检查)
- [ ] 实现重定向逻辑

**交付物：**
- 完整的认证流程
- 30 天缓存登录
- 飞书 OAuth 集成

---

### 阶段 3: 任务模块 (Day 5-7)

#### 3.1 Tasks Slice

- [ ] 定义 Task 类型
- [ ] 定义 TasksState 类型
- [ ] 实现 tasksSlice
  - [ ] `setTasks` - 设置任务列表
  - [ ] `addTask` - 添加任务
  - [ ] `updateTask` - 更新任务
  - [ ] `removeTask` - 移除任务
  - [ ] `selectTask` - 选择任务
- [ ] 实现异步 thunks
  - [ ] `fetchPendingTasks` - 获取待处理任务
  - [ ] `fetchHistory` - 获取历史记录
  - [ ] `submitReply` - 提交回复
  - [ ] `dismissTask` - 忽略任务

#### 3.2 页面组件

- [ ] TasksPage - 任务主页
- [ ] TaskList - 任务列表
- [ ] TaskItem - 任务项
- [ ] TaskDetail - 任务详情
- [ ] ReplyForm - 回复表单
  - [ ] 文本输入
  - [ ] 图片上传
  - [ ] 粘贴截图
- [ ] HistoryList - 历史记录列表
- [ ] HistoryItem - 历史记录项

#### 3.3 功能实现

- [ ] 轮询机制 (2秒间隔)
- [ ] 浏览器通知
- [ ] 任务自动选择
- [ ] 历史记录删除
- [ ] 批量删除

#### 3.4 Hooks

- [ ] `usePolling` - 轮询管理
- [ ] `useNotification` - 浏览器通知

**交付物：**
- 完整的任务管理功能
- 实时轮询
- 图文回复

---

### 阶段 4: 用户模块 (Day 8)

#### 4.1 User Slice

- [ ] 定义 UserProfile 类型
- [ ] 定义 UserState 类型
- [ ] 实现 userSlice
  - [ ] `setProfile` - 设置用户信息
  - [ ] `setFeishuNotify` - 设置飞书通知
  - [ ] `clearProfile` - 清除用户信息
- [ ] 实现异步 thunks
  - [ ] `fetchUserInfo` - 获取用户信息
  - [ ] `updateFeishuNotify` - 更新飞书通知状态
  - [ ] `regenerateApiKey` - 重新生成 API Key

#### 4.2 页面组件

- [ ] UserPage - 用户中心
- [ ] UserProfile - 用户信息卡片
- [ ] ApiKeyDisplay - API Key 显示
- [ ] FeishuNotifyToggle - 飞书通知开关
- [ ] McpConfigPreview - MCP 配置示例

**交付物：**
- 用户中心页面
- API Key 管理
- 飞书通知设置

---

### 阶段 5: 管理后台 (Day 9-10)

#### 5.1 Admin Slice

- [ ] 定义 AdminState 类型
- [ ] 实现 adminSlice
  - [ ] `setSessionToken` - 设置会话令牌
  - [ ] `clearSession` - 清除会话
  - [ ] `setUsers` - 设置用户列表
  - [ ] `setStats` - 设置统计信息
- [ ] 实现异步 thunks
  - [ ] `adminLogin` - 管理员登录
  - [ ] `adminLogout` - 管理员登出
  - [ ] `fetchUsers` - 获取用户列表
  - [ ] `updateFeishuConfig` - 更新飞书配置
  - [ ] `changePassword` - 修改密码

#### 5.2 页面组件

- [ ] AdminPage - 管理后台
- [ ] AdminSidebar - 侧边栏
- [ ] SystemConfig - 系统配置
- [ ] FeishuConfig - 飞书配置
- [ ] PasswordChange - 密码修改
- [ ] UserManagement - 用户管理
- [ ] SystemStats - 系统状态

**交付物：**
- 管理后台
- 飞书配置管理
- 用户管理

---

### 阶段 6: 测试与优化 (Day 11-12)

#### 6.1 单元测试

- [ ] Redux Slice 测试
- [ ] 工具函数测试
- [ ] Hooks 测试

#### 6.2 组件测试

- [ ] 基础组件测试
- [ ] 页面组件测试
- [ ] 用户交互测试

#### 6.3 集成测试

- [ ] 认证流程测试
- [ ] 任务流程测试
- [ ] API 集成测试

#### 6.4 性能优化

- [ ] 代码分割
- [ ] 懒加载
- [ ] 缓存优化
- [ ] Bundle 分析

#### 6.5 文档完善

- [ ] 组件文档
- [ ] API 文档
- [ ] 部署文档

**交付物：**
- 测试报告
- 性能报告
- 完整文档

---

## 里程碑

| 里程碑 | 日期 | 交付物 |
|--------|------|--------|
| M1 - 基础设施 | Day 2 | 可运行的 React 项目 |
| M2 - 认证模块 | Day 4 | 登录/登出功能 |
| M3 - 任务模块 | Day 7 | 任务管理功能 |
| M4 - 用户/管理 | Day 10 | 完整功能 |
| M5 - 测试完成 | Day 12 | 生产就绪 |

## 每日交付

每天结束时需要：

1. **代码提交** - 有意义的 commit message
2. **测试通过** - 新增代码有测试覆盖
3. **文档更新** - 更新相关文档
4. **进度更新** - 更新本文档的完成状态

## 技术决策记录

### TD-001: 使用 Redux Toolkit

**决策**: 使用 Redux Toolkit 而非纯 Redux

**原因**:
- 减少样板代码
- 内置 Immer 支持不可变更新
- 内置 createAsyncThunk 处理异步
- 官方推荐的最佳实践

### TD-002: 使用 Vite

**决策**: 使用 Vite 而非 Create React App

**原因**:
- 开发服务器启动更快
- HMR 更快
- 构建产物更小
- 原生 ESM 支持

### TD-003: 使用 TailwindCSS

**决策**: 使用 TailwindCSS 而非 CSS Modules

**原因**:
- 与现有 HTML 模板样式一致
- 快速开发
- 无需命名类名
- 生产环境自动 PurgeCSS

### TD-004: API Key 存储

**决策**: 使用 localStorage 存储 API Key

**原因**:
- 30 天缓存需求
- 跨会话持久化
- 简单可靠

**安全考虑**:
- API Key 只用于用户自己的消息隔离
- 不涉及敏感操作权限
- 用户可随时重新生成
