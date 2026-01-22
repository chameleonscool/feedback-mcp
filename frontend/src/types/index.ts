// Auth types
export interface AuthState {
  apiKey: string | null;
  apiKeyExpiry: number | null;
  isAuthenticated: boolean;
  loginStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
}

// User types
export interface UserProfile {
  openId: string;
  name: string;
  avatarUrl?: string;
  email?: string;
  isActive: boolean;
}

export interface UserState {
  profile: UserProfile | null;
  feishuNotifyEnabled: boolean;
  loadingStatus: 'idle' | 'loading' | 'succeeded' | 'failed';
}

// Task types
export interface Task {
  id: string;
  question: string;
  status: 'PENDING' | 'COMPLETED' | 'DISMISSED';
  answer?: string;
  image?: string;
  createdAt?: string;
  completedAt?: string;
}

export interface TasksState {
  pending: Task[];
  history: Task[];
  selectedTaskId: string | null;
  pollingStatus: 'idle' | 'polling' | 'paused' | 'error';
}

// Admin types
export interface AdminState {
  sessionToken: string | null;
  isAuthenticated: boolean;
  users: AdminUser[];
  stats: SystemStats | null;
}

export interface AdminUser {
  openId: string;
  name: string;
  email?: string;
  isActive: boolean;
  createdAt: string;
}

export interface SystemStats {
  userCount: number;
  todayRequests: number;
  version: string;
}

// UI types
export interface UIState {
  theme: 'light' | 'dark';
  language: 'zh' | 'en';
  sidebarOpen: boolean;
}
