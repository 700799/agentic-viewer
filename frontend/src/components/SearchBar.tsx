import { useEffect } from "react";
import type { GraphNode } from "@/types/api";
import { useCanvasStore } from "@/store/canvasStore";

// Simple, dependency-free fuzzy-ish search: case-insensitive substring over node
// labels, agent names, models and file paths. (Fuse.js ranking is a V1 upgrade.)
export function SearchBar({ nodes }: { nodes: GraphNode[] }) {
  const query = useCanvasStore((s) => s.searchQuery);
  const setQuery = useCanvasStore((s) => s.setSearchQuery);
  const setHighlight = useCanvasStore((s) => s.setHighlight);

  useEffect(() => {
    const q = query.trim().toLowerCase();
    if (!q) {
      setHighlight([]);
      return;
    }
    const matches = nodes
      .filter((n) => {
        const hay = [n.label, n.data.agentName, n.data.model, n.data.path, n.data.kind]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .map((n) => n.id);
    setHighlight(matches);
  }, [query, nodes, setHighlight]);

  return (
    <input
      className="search"
      placeholder="Search nodes…"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
    />
  );
}
