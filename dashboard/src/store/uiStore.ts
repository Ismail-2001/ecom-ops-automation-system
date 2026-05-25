import { create } from 'zustand';

interface Filters {
  agent: string;
  risk: string;
  status: string;
}

interface UIState {
  selectedActionId: string | null;
  searchQuery: string;
  filters: Filters;
  sort: string;
  selectedActionIds: string[];
  keyboardHelpOpen: boolean;
  
  // Actions
  setSelectedActionId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  setFilter: (key: keyof Filters, value: string) => void;
  resetFilters: () => void;
  setSort: (sort: string) => void;
  
  // Batch selections
  toggleSelectedActionId: (id: string) => void;
  setSelectedActionIds: (ids: string[]) => void;
  clearSelection: () => void;
  
  // Help overlay
  setKeyboardHelpOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedActionId: null,
  searchQuery: '',
  filters: {
    agent: 'all',
    risk: 'all',
    status: 'pending',
  },
  sort: 'newest',
  selectedActionIds: [],
  keyboardHelpOpen: false,

  setSelectedActionId: (id) => set({ selectedActionId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      // Clear batch selection on filter changes to prevent accidental batch actions
      selectedActionIds: [],
    })),
  resetFilters: () =>
    set({
      filters: {
        agent: 'all',
        risk: 'all',
        status: 'pending',
      },
      selectedActionIds: [],
    }),
  setSort: (sort) => set({ sort }),

  toggleSelectedActionId: (id) =>
    set((state) => {
      const idx = state.selectedActionIds.indexOf(id);
      if (idx > -1) {
        return { selectedActionIds: state.selectedActionIds.filter((x) => x !== id) };
      } else {
        return { selectedActionIds: [...state.selectedActionIds, id] };
      }
    }),
  setSelectedActionIds: (ids) => set({ selectedActionIds: ids }),
  clearSelection: () => set({ selectedActionIds: [] }),
  
  setKeyboardHelpOpen: (open) => set({ keyboardHelpOpen: open }),
}));
