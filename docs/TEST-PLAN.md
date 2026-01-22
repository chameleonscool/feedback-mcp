# TDD 测试计划

## 测试原则

遵循 TDD (Test-Driven Development) 开发流程：

1. **Red** - 先写测试，测试失败
2. **Green** - 写最少的代码让测试通过
3. **Refactor** - 重构代码，保持测试通过

## 测试工具

| 工具 | 用途 |
|------|------|
| Vitest | 单元测试、集成测试 |
| React Testing Library | 组件测试 |
| MSW (Mock Service Worker) | API Mock |
| @testing-library/user-event | 用户交互模拟 |

## 测试目录结构

```
frontend/
├── src/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── authSlice.ts
│   │   │   └── authSlice.test.ts      # Slice 测试
│   │   ├── tasks/
│   │   │   ├── tasksSlice.ts
│   │   │   └── tasksSlice.test.ts
│   │   └── ...
│   │
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   └── Button.test.tsx        # 组件测试
│   │   └── ...
│   │
│   └── utils/
│       ├── storage.ts
│       └── storage.test.ts            # 工具测试
│
├── tests/
│   ├── setup.ts                       # 测试配置
│   ├── mocks/
│   │   ├── handlers.ts                # MSW handlers
│   │   └── server.ts                  # MSW server
│   └── integration/
│       ├── auth.test.tsx              # 认证集成测试
│       └── tasks.test.tsx             # 任务集成测试
│
└── vitest.config.ts
```

---

## 1. Auth Slice 测试

### 1.1 初始状态测试

```typescript
// features/auth/authSlice.test.ts

describe('authSlice', () => {
  describe('initial state', () => {
    it('should have null apiKey initially', () => {
      const state = authReducer(undefined, { type: 'unknown' });
      expect(state.apiKey).toBeNull();
    });

    it('should have null apiKeyExpiry initially', () => {
      const state = authReducer(undefined, { type: 'unknown' });
      expect(state.apiKeyExpiry).toBeNull();
    });

    it('should not be authenticated initially', () => {
      const state = authReducer(undefined, { type: 'unknown' });
      expect(state.isAuthenticated).toBe(false);
    });
  });
});
```

### 1.2 Actions 测试

```typescript
describe('actions', () => {
  describe('setApiKey', () => {
    it('should set apiKey and isAuthenticated', () => {
      const state = authReducer(undefined, setApiKey('uk_test123'));
      expect(state.apiKey).toBe('uk_test123');
      expect(state.isAuthenticated).toBe(true);
    });

    it('should set apiKeyExpiry to 30 days from now', () => {
      const before = Date.now();
      const state = authReducer(undefined, setApiKey('uk_test123'));
      const after = Date.now();
      
      const thirtyDays = 30 * 24 * 60 * 60 * 1000;
      expect(state.apiKeyExpiry).toBeGreaterThanOrEqual(before + thirtyDays);
      expect(state.apiKeyExpiry).toBeLessThanOrEqual(after + thirtyDays);
    });
  });

  describe('clearApiKey', () => {
    it('should clear apiKey and set isAuthenticated to false', () => {
      const initialState = {
        apiKey: 'uk_test123',
        apiKeyExpiry: Date.now() + 1000000,
        isAuthenticated: true,
        loginStatus: 'succeeded' as const,
      };
      const state = authReducer(initialState, clearApiKey());
      expect(state.apiKey).toBeNull();
      expect(state.apiKeyExpiry).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('loadCachedAuth', () => {
    it('should load valid cached auth', () => {
      const futureExpiry = Date.now() + 1000000;
      localStorage.setItem('userApiKey', 'uk_cached');
      localStorage.setItem('userApiKeyExpiry', String(futureExpiry));

      const state = authReducer(undefined, loadCachedAuth());
      expect(state.apiKey).toBe('uk_cached');
      expect(state.isAuthenticated).toBe(true);
    });

    it('should not load expired cached auth', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));

      const state = authReducer(undefined, loadCachedAuth());
      expect(state.apiKey).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('should clear localStorage when expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));

      authReducer(undefined, loadCachedAuth());
      expect(localStorage.getItem('userApiKey')).toBeNull();
      expect(localStorage.getItem('userApiKeyExpiry')).toBeNull();
    });
  });
});
```

---

## 2. Tasks Slice 测试

### 2.1 Reducers 测试

```typescript
// features/tasks/tasksSlice.test.ts

describe('tasksSlice', () => {
  describe('setTasks', () => {
    it('should set pending tasks', () => {
      const tasks = [
        { id: '1', question: 'Q1', status: 'PENDING' },
        { id: '2', question: 'Q2', status: 'PENDING' },
      ];
      const state = tasksReducer(undefined, setTasks(tasks));
      expect(state.pending).toEqual(tasks);
    });
  });

  describe('selectTask', () => {
    it('should set selectedTaskId', () => {
      const state = tasksReducer(undefined, selectTask('task-1'));
      expect(state.selectedTaskId).toBe('task-1');
    });

    it('should clear selectedTaskId when passed null', () => {
      const initialState = { ...defaultState, selectedTaskId: 'task-1' };
      const state = tasksReducer(initialState, selectTask(null));
      expect(state.selectedTaskId).toBeNull();
    });
  });

  describe('addTask', () => {
    it('should add task to beginning of pending list', () => {
      const initialState = {
        ...defaultState,
        pending: [{ id: '1', question: 'Q1', status: 'PENDING' }],
      };
      const newTask = { id: '2', question: 'Q2', status: 'PENDING' };
      const state = tasksReducer(initialState, addTask(newTask));
      expect(state.pending[0]).toEqual(newTask);
      expect(state.pending).toHaveLength(2);
    });
  });

  describe('removeTask', () => {
    it('should remove task from pending list', () => {
      const initialState = {
        ...defaultState,
        pending: [
          { id: '1', question: 'Q1', status: 'PENDING' },
          { id: '2', question: 'Q2', status: 'PENDING' },
        ],
      };
      const state = tasksReducer(initialState, removeTask('1'));
      expect(state.pending).toHaveLength(1);
      expect(state.pending[0].id).toBe('2');
    });

    it('should clear selectedTaskId if removed task was selected', () => {
      const initialState = {
        ...defaultState,
        pending: [{ id: '1', question: 'Q1', status: 'PENDING' }],
        selectedTaskId: '1',
      };
      const state = tasksReducer(initialState, removeTask('1'));
      expect(state.selectedTaskId).toBeNull();
    });
  });
});
```

### 2.2 Async Thunks 测试

```typescript
describe('async thunks', () => {
  describe('fetchPendingTasks', () => {
    it('should fetch and set pending tasks', async () => {
      server.use(
        rest.get('/api/poll', (req, res, ctx) => {
          return res(ctx.json([
            { id: '1', question: 'Task 1' },
            { id: '2', question: 'Task 2' },
          ]));
        })
      );

      const store = configureStore({ reducer: { tasks: tasksReducer } });
      await store.dispatch(fetchPendingTasks());
      
      const state = store.getState().tasks;
      expect(state.pending).toHaveLength(2);
    });

    it('should handle API error', async () => {
      server.use(
        rest.get('/api/poll', (req, res, ctx) => {
          return res(ctx.status(500));
        })
      );

      const store = configureStore({ reducer: { tasks: tasksReducer } });
      await store.dispatch(fetchPendingTasks());
      
      const state = store.getState().tasks;
      expect(state.pollingStatus).toBe('error');
    });
  });

  describe('submitReply', () => {
    it('should submit reply and remove task', async () => {
      server.use(
        rest.post('/api/reply', (req, res, ctx) => {
          return res(ctx.json({ status: 'success' }));
        })
      );

      const initialState = {
        pending: [{ id: '1', question: 'Q1', status: 'PENDING' }],
        selectedTaskId: '1',
      };
      const store = configureStore({
        reducer: { tasks: tasksReducer },
        preloadedState: { tasks: initialState },
      });

      await store.dispatch(submitReply({ id: '1', answer: 'Answer' }));
      
      const state = store.getState().tasks;
      expect(state.pending).toHaveLength(0);
    });
  });
});
```

---

## 3. 组件测试

### 3.1 Button 组件

```typescript
// components/Button/Button.test.tsx

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    await userEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByText('Click me')).toBeDisabled();
  });

  it('shows spinner when loading', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });

  it('applies variant styles', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByText('Primary')).toHaveClass('bg-blue-600');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-gray-600');
  });
});
```

### 3.2 LoginPage 组件

```typescript
// features/auth/LoginPage.test.tsx

describe('LoginPage', () => {
  it('renders login options', () => {
    render(<LoginPage />, { wrapper: TestProviders });
    
    expect(screen.getByText('使用飞书登录')).toBeInTheDocument();
    expect(screen.getByText('管理员登录')).toBeInTheDocument();
    expect(screen.getByText('使用 Web UI')).toBeInTheDocument();
  });

  it('redirects to feishu oauth on button click', async () => {
    render(<LoginPage />, { wrapper: TestProviders });
    
    await userEvent.click(screen.getByText('使用飞书登录'));
    expect(window.location.href).toContain('/auth/feishu/login');
  });

  it('navigates to admin login page', async () => {
    const { history } = renderWithRouter(<LoginPage />);
    
    await userEvent.click(screen.getByText('管理员登录'));
    expect(history.location.pathname).toBe('/admin/login');
  });
});
```

### 3.3 TaskList 组件

```typescript
// features/tasks/components/TaskList.test.tsx

describe('TaskList', () => {
  const mockTasks = [
    { id: '1', question: 'First question?' },
    { id: '2', question: 'Second question?' },
  ];

  it('renders all tasks', () => {
    render(<TaskList tasks={mockTasks} />, { wrapper: TestProviders });
    
    expect(screen.getByText('First question?')).toBeInTheDocument();
    expect(screen.getByText('Second question?')).toBeInTheDocument();
  });

  it('shows empty state when no tasks', () => {
    render(<TaskList tasks={[]} />, { wrapper: TestProviders });
    
    expect(screen.getByText('暂无待处理任务')).toBeInTheDocument();
  });

  it('highlights selected task', () => {
    render(
      <TaskList tasks={mockTasks} selectedId="1" />,
      { wrapper: TestProviders }
    );
    
    const selectedTask = screen.getByText('First question?').closest('div');
    expect(selectedTask).toHaveClass('ring-2', 'ring-blue-500');
  });

  it('calls onSelect when task is clicked', async () => {
    const handleSelect = vi.fn();
    render(
      <TaskList tasks={mockTasks} onSelect={handleSelect} />,
      { wrapper: TestProviders }
    );
    
    await userEvent.click(screen.getByText('First question?'));
    expect(handleSelect).toHaveBeenCalledWith('1');
  });
});
```

### 3.4 ReplyForm 组件

```typescript
// features/tasks/components/ReplyForm.test.tsx

describe('ReplyForm', () => {
  it('renders textarea and submit button', () => {
    render(<ReplyForm taskId="1" />, { wrapper: TestProviders });
    
    expect(screen.getByPlaceholderText('输入您的回复...')).toBeInTheDocument();
    expect(screen.getByText('提交')).toBeInTheDocument();
  });

  it('enables submit button when text is entered', async () => {
    render(<ReplyForm taskId="1" />, { wrapper: TestProviders });
    
    const textarea = screen.getByPlaceholderText('输入您的回复...');
    const submitBtn = screen.getByText('提交');

    expect(submitBtn).toBeDisabled();
    
    await userEvent.type(textarea, 'My reply');
    expect(submitBtn).toBeEnabled();
  });

  it('submits reply on form submit', async () => {
    const store = configureStore({ reducer: rootReducer });
    render(<ReplyForm taskId="1" />, { wrapper: createTestWrapper(store) });
    
    await userEvent.type(screen.getByPlaceholderText('输入您的回复...'), 'My reply');
    await userEvent.click(screen.getByText('提交'));
    
    // Check that API was called
    await waitFor(() => {
      expect(store.getState().tasks.pending).not.toContainEqual(
        expect.objectContaining({ id: '1' })
      );
    });
  });

  it('handles image paste', async () => {
    render(<ReplyForm taskId="1" />, { wrapper: TestProviders });
    
    const textarea = screen.getByPlaceholderText('输入您的回复...');
    
    // Simulate paste event with image
    const pasteEvent = createPasteEvent(mockImageFile);
    fireEvent.paste(textarea, pasteEvent);
    
    await waitFor(() => {
      expect(screen.getByAltText('Pasted image')).toBeInTheDocument();
    });
  });
});
```

---

## 4. 工具函数测试

### 4.1 Storage 工具

```typescript
// utils/storage.test.ts

describe('storage utils', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('saveApiKey', () => {
    it('saves apiKey to localStorage', () => {
      saveApiKey('uk_test');
      expect(localStorage.getItem('userApiKey')).toBe('uk_test');
    });

    it('saves expiry date', () => {
      const before = Date.now();
      saveApiKey('uk_test');
      const after = Date.now();
      
      const expiry = Number(localStorage.getItem('userApiKeyExpiry'));
      const thirtyDays = 30 * 24 * 60 * 60 * 1000;
      
      expect(expiry).toBeGreaterThanOrEqual(before + thirtyDays);
      expect(expiry).toBeLessThanOrEqual(after + thirtyDays);
    });
  });

  describe('getApiKey', () => {
    it('returns apiKey if not expired', () => {
      const futureExpiry = Date.now() + 1000000;
      localStorage.setItem('userApiKey', 'uk_valid');
      localStorage.setItem('userApiKeyExpiry', String(futureExpiry));
      
      expect(getApiKey()).toBe('uk_valid');
    });

    it('returns null if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));
      
      expect(getApiKey()).toBeNull();
    });

    it('clears storage if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKey', 'uk_expired');
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));
      
      getApiKey();
      
      expect(localStorage.getItem('userApiKey')).toBeNull();
    });
  });

  describe('clearApiKey', () => {
    it('removes apiKey from localStorage', () => {
      localStorage.setItem('userApiKey', 'uk_test');
      localStorage.setItem('userApiKeyExpiry', '123');
      
      clearApiKey();
      
      expect(localStorage.getItem('userApiKey')).toBeNull();
      expect(localStorage.getItem('userApiKeyExpiry')).toBeNull();
    });
  });

  describe('getRemainingDays', () => {
    it('returns correct remaining days', () => {
      const tenDaysLater = Date.now() + 10 * 24 * 60 * 60 * 1000;
      localStorage.setItem('userApiKeyExpiry', String(tenDaysLater));
      
      expect(getRemainingDays()).toBe(10);
    });

    it('returns 0 if expired', () => {
      const pastExpiry = Date.now() - 1000;
      localStorage.setItem('userApiKeyExpiry', String(pastExpiry));
      
      expect(getRemainingDays()).toBe(0);
    });
  });
});
```

---

## 5. 集成测试

### 5.1 认证流程测试

```typescript
// tests/integration/auth.test.tsx

describe('Authentication Flow', () => {
  it('shows login page when not authenticated', async () => {
    render(<App />, { wrapper: TestProviders });
    
    await waitFor(() => {
      expect(screen.getByText('使用飞书登录')).toBeInTheDocument();
    });
  });

  it('shows cached login when apiKey is cached', async () => {
    saveApiKey('uk_cached');
    server.use(
      rest.get('/api/user/info', (req, res, ctx) => {
        return res(ctx.json({ name: 'Test User' }));
      })
    );

    render(<App />, { wrapper: TestProviders });
    
    await waitFor(() => {
      expect(screen.getByText('欢迎回来')).toBeInTheDocument();
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });

  it('redirects to tasks page on continue', async () => {
    saveApiKey('uk_cached');
    server.use(
      rest.get('/api/user/info', (req, res, ctx) => {
        return res(ctx.json({ name: 'Test User' }));
      })
    );

    render(<App />, { wrapper: TestProviders });
    
    await waitFor(() => {
      expect(screen.getByText('继续使用')).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByText('继续使用'));
    
    await waitFor(() => {
      expect(screen.getByText('待处理任务')).toBeInTheDocument();
    });
  });

  it('clears cache and shows login on logout', async () => {
    saveApiKey('uk_cached');
    server.use(
      rest.get('/api/user/info', (req, res, ctx) => {
        return res(ctx.json({ name: 'Test User' }));
      })
    );

    render(<App />, { wrapper: TestProviders });
    
    await userEvent.click(screen.getByText('退出登录'));
    
    await waitFor(() => {
      expect(screen.getByText('使用飞书登录')).toBeInTheDocument();
    });
    
    expect(getApiKey()).toBeNull();
  });
});
```

### 5.2 任务流程测试

```typescript
// tests/integration/tasks.test.tsx

describe('Task Management Flow', () => {
  beforeEach(() => {
    saveApiKey('uk_test');
  });

  it('displays pending tasks from API', async () => {
    server.use(
      rest.get('/api/poll', (req, res, ctx) => {
        return res(ctx.json([
          { id: '1', question: 'First task?' },
          { id: '2', question: 'Second task?' },
        ]));
      })
    );

    render(<TasksPage />, { wrapper: TestProviders });
    
    await waitFor(() => {
      expect(screen.getByText('First task?')).toBeInTheDocument();
      expect(screen.getByText('Second task?')).toBeInTheDocument();
    });
  });

  it('selects first task by default', async () => {
    server.use(
      rest.get('/api/poll', (req, res, ctx) => {
        return res(ctx.json([
          { id: '1', question: 'First task?' },
        ]));
      })
    );

    render(<TasksPage />, { wrapper: TestProviders });
    
    await waitFor(() => {
      const taskItem = screen.getByText('First task?').closest('div');
      expect(taskItem).toHaveClass('ring-blue-500');
    });
  });

  it('submits reply and removes task', async () => {
    server.use(
      rest.get('/api/poll', (req, res, ctx) => {
        return res.once(ctx.json([
          { id: '1', question: 'Task to reply?' },
        ]));
      }),
      rest.post('/api/reply', (req, res, ctx) => {
        return res(ctx.json({ status: 'success' }));
      }),
      rest.get('/api/poll', (req, res, ctx) => {
        return res(ctx.json([]));
      })
    );

    render(<TasksPage />, { wrapper: TestProviders });
    
    await waitFor(() => {
      expect(screen.getByText('Task to reply?')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText('输入您的回复...'), 'My answer');
    await userEvent.click(screen.getByText('提交'));
    
    await waitFor(() => {
      expect(screen.queryByText('Task to reply?')).not.toBeInTheDocument();
    });
  });

  it('shows notification for new task', async () => {
    const notificationSpy = vi.spyOn(window.Notification.prototype, 'constructor');
    
    server.use(
      rest.get('/api/poll', (req, res, ctx) => {
        return res.once(ctx.json([]));
      }),
      rest.get('/api/poll', (req, res, ctx) => {
        return res(ctx.json([
          { id: '1', question: 'New task!' },
        ]));
      })
    );

    render(<TasksPage />, { wrapper: TestProviders });
    
    // Wait for second poll
    await waitFor(() => {
      expect(notificationSpy).toHaveBeenCalledWith(
        'AI Intent Request',
        expect.objectContaining({ body: expect.stringContaining('New task!') })
      );
    }, { timeout: 3000 });
  });
});
```

---

## 6. 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| Redux Slices | 90%+ |
| Utils | 95%+ |
| Components | 80%+ |
| Pages | 70%+ |
| 总体 | 80%+ |

## 7. 测试命令

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- authSlice.test.ts

# 运行测试并生成覆盖率报告
npm run test:coverage

# 监听模式
npm run test:watch

# 运行集成测试
npm run test:integration
```

## 8. CI 集成

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      
      - name: Install dependencies
        run: cd frontend && pnpm install
      
      - name: Run tests
        run: cd frontend && pnpm test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/lcov.info
```
