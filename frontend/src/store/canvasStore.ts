// Canvas + replay UI state shared across the DAG and Timeline views.
// Server state lives in TanStack Query; this is purely transient interaction state.

import { create } from "zustand";

interface CanvasState {
  // Currently selected span (drives the detail drawer + node highlight).
  selectedSpanId: string | null;
  // Replay cursor: the highest sequence revealed so far. Shared by timeline + canvas.
  replayCursor: number | null;
  // Fuzzy-search highlight set (node ids).
  highlightIds: Set<string>;
  // Collapsed agent groups (group ids).
  collapsedGroups: Set<string>;
  searchQuery: string;

  setSelected: (id: string | null) => void;
  setReplayCursor: (seq: number | null) => void;
  setHighlight: (ids: string[]) => void;
  toggleGroup: (groupId: string) => void;
  setSearchQuery: (q: string) => void;
  reset: () => void;
}

export const useCanvasStore = create<CanvasState>((set) => ({
  selectedSpanId: null,
  replayCursor: null,
  highlightIds: new Set(),
  collapsedGroups: new Set(),
  searchQuery: "",

  setSelected: (id) => set({ selectedSpanId: id }),
  setReplayCursor: (seq) => set({ replayCursor: seq }),
  setHighlight: (ids) => set({ highlightIds: new Set(ids) }),
  toggleGroup: (groupId) =>
    set((s) => {
      const next = new Set(s.collapsedGroups);
      if (next.has(groupId)) next.delete(groupId);
      else next.add(groupId);
      return { collapsedGroups: next };
    }),
  setSearchQuery: (q) => set({ searchQuery: q }),
  reset: () =>
    set({
      selectedSpanId: null,
      replayCursor: null,
      highlightIds: new Set(),
      collapsedGroups: new Set(),
      searchQuery: "",
    }),
}));
