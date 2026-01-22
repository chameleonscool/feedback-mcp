import { describe, it, expect } from 'vitest';
import tasksReducer, {
  setTasks,
  addTask,
  removeTask,
  selectTask,
  setPollingStatus,
  clearHistory,
} from './tasksSlice';
import type { TasksState, Task } from '@/types';

describe('tasksSlice', () => {
  const initialState: TasksState = {
    pending: [],
    history: [],
    selectedTaskId: null,
    pollingStatus: 'idle',
  };

  const mockTask: Task = {
    id: 'task-1',
    question: 'Test question?',
    status: 'PENDING',
  };

  const mockTask2: Task = {
    id: 'task-2',
    question: 'Another question?',
    status: 'PENDING',
  };

  describe('setTasks', () => {
    it('should set pending tasks', () => {
      const state = tasksReducer(initialState, setTasks([mockTask, mockTask2]));

      expect(state.pending).toHaveLength(2);
      expect(state.pending[0].id).toBe('task-1');
      expect(state.pending[1].id).toBe('task-2');
    });
  });

  describe('addTask', () => {
    it('should add task to the beginning of pending list', () => {
      const stateWithTask = { ...initialState, pending: [mockTask] };
      const state = tasksReducer(stateWithTask, addTask(mockTask2));

      expect(state.pending).toHaveLength(2);
      expect(state.pending[0].id).toBe('task-2'); // New task first
      expect(state.pending[1].id).toBe('task-1');
    });
  });

  describe('removeTask', () => {
    it('should remove task from pending list', () => {
      const stateWithTasks = {
        ...initialState,
        pending: [mockTask, mockTask2],
      };
      const state = tasksReducer(stateWithTasks, removeTask('task-1'));

      expect(state.pending).toHaveLength(1);
      expect(state.pending[0].id).toBe('task-2');
    });

    it('should clear selected task if removed', () => {
      const stateWithSelection = {
        ...initialState,
        pending: [mockTask, mockTask2],
        selectedTaskId: 'task-1',
      };
      const state = tasksReducer(stateWithSelection, removeTask('task-1'));

      expect(state.selectedTaskId).toBe('task-2'); // Auto-select next
    });

    it('should set selectedTaskId to null if no tasks remain', () => {
      const stateWithOneTask = {
        ...initialState,
        pending: [mockTask],
        selectedTaskId: 'task-1',
      };
      const state = tasksReducer(stateWithOneTask, removeTask('task-1'));

      expect(state.selectedTaskId).toBeNull();
    });
  });

  describe('selectTask', () => {
    it('should select a task', () => {
      const state = tasksReducer(initialState, selectTask('task-1'));
      expect(state.selectedTaskId).toBe('task-1');
    });

    it('should allow deselecting', () => {
      const stateWithSelection = {
        ...initialState,
        selectedTaskId: 'task-1',
      };
      const state = tasksReducer(stateWithSelection, selectTask(null));
      expect(state.selectedTaskId).toBeNull();
    });
  });

  describe('setPollingStatus', () => {
    it('should set polling status', () => {
      const state = tasksReducer(initialState, setPollingStatus('polling'));
      expect(state.pollingStatus).toBe('polling');
    });
  });

  describe('clearHistory', () => {
    it('should clear history', () => {
      const stateWithHistory = {
        ...initialState,
        history: [{ ...mockTask, status: 'COMPLETED' as const }],
      };
      const state = tasksReducer(stateWithHistory, clearHistory());
      expect(state.history).toHaveLength(0);
    });
  });
});
