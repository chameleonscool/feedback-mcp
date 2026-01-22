import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import type { Task, TasksState } from '@/types';
import { api } from '@/services/api';

const initialState: TasksState = {
  pending: [],
  history: [],
  selectedTaskId: null,
  selectedHistoryId: null,
  pollingStatus: 'idle',
};

/**
 * 获取待处理任务
 */
export const fetchPendingTasks = createAsyncThunk(
  'tasks/fetchPending',
  async () => {
    const response = await api.get<Task[]>('/api/poll');
    return response.data;
  }
);

/**
 * 获取历史记录
 */
export const fetchHistory = createAsyncThunk(
  'tasks/fetchHistory',
  async () => {
    const response = await api.get<Task[]>('/api/history');
    return response.data;
  }
);

/**
 * 提交回复
 */
export const submitReply = createAsyncThunk(
  'tasks/submitReply',
  async (payload: { id: string; answer: string; image?: string }) => {
    await api.post('/api/reply', payload);
    return payload.id;
  }
);

/**
 * 忽略任务
 */
export const dismissTask = createAsyncThunk(
  'tasks/dismiss',
  async (taskId: string) => {
    await api.post('/api/dismiss', { id: taskId });
    return taskId;
  }
);

export const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    /**
     * 设置任务列表
     */
    setTasks: (state, action: PayloadAction<Task[]>) => {
      state.pending = action.payload;
    },

    /**
     * 添加任务
     */
    addTask: (state, action: PayloadAction<Task>) => {
      state.pending.unshift(action.payload);
    },

    /**
     * 移除任务
     */
    removeTask: (state, action: PayloadAction<string>) => {
      const taskId = action.payload;
      state.pending = state.pending.filter((t) => t.id !== taskId);
      
      // 如果移除的是当前选中的任务，清除选中状态
      if (state.selectedTaskId === taskId) {
        state.selectedTaskId = state.pending[0]?.id ?? null;
      }
    },

    /**
     * 选择任务
     */
    selectTask: (state, action: PayloadAction<string | null>) => {
      state.selectedTaskId = action.payload;
    },

    /**
     * 选择历史记录
     */
    selectHistoryItem: (state, action: PayloadAction<string | null>) => {
      state.selectedHistoryId = action.payload;
    },

    /**
     * 设置轮询状态
     */
    setPollingStatus: (state, action: PayloadAction<TasksState['pollingStatus']>) => {
      state.pollingStatus = action.payload;
    },

    /**
     * 清空历史记录
     */
    clearHistory: (state) => {
      state.history = [];
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchPendingTasks
      .addCase(fetchPendingTasks.pending, (state) => {
        state.pollingStatus = 'polling';
      })
      .addCase(fetchPendingTasks.fulfilled, (state, action) => {
        state.pending = action.payload;
        state.pollingStatus = 'idle';
        
        // 如果没有选中任务且有待处理任务，自动选中第一个
        if (!state.selectedTaskId && action.payload.length > 0) {
          state.selectedTaskId = action.payload[0].id;
        }
      })
      .addCase(fetchPendingTasks.rejected, (state) => {
        state.pollingStatus = 'error';
      })
      
      // fetchHistory
      .addCase(fetchHistory.fulfilled, (state, action) => {
        state.history = action.payload;
      })
      
      // submitReply
      .addCase(submitReply.fulfilled, (state, action) => {
        const taskId = action.payload;
        state.pending = state.pending.filter((t) => t.id !== taskId);
        
        if (state.selectedTaskId === taskId) {
          state.selectedTaskId = state.pending[0]?.id ?? null;
        }
      })
      
      // dismissTask
      .addCase(dismissTask.fulfilled, (state, action) => {
        const taskId = action.payload;
        state.pending = state.pending.filter((t) => t.id !== taskId);
        
        if (state.selectedTaskId === taskId) {
          state.selectedTaskId = state.pending[0]?.id ?? null;
        }
      });
  },
});

export const {
  setTasks,
  addTask,
  removeTask,
  selectTask,
  selectHistoryItem,
  setPollingStatus,
  clearHistory,
} = tasksSlice.actions;

export default tasksSlice.reducer;
