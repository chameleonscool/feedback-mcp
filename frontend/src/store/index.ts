import { configureStore } from '@reduxjs/toolkit';
import authReducer from '@/features/auth/authSlice';
import tasksReducer from '@/features/tasks/tasksSlice';
import userReducer from '@/features/user/userSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    tasks: tasksReducer,
    user: userReducer,
  },
  devTools: import.meta.env.DEV,
});

// 类型推断
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
