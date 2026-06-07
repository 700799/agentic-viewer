// TanStack Query hooks — one per API resource. Query keys are stable so the
// comparison view and others can share/cache fetched sessions.

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "./client";
import type {
  CompareReport,
  CostReport,
  DiagramResponse,
  GraphResponse,
  SessionList,
  SessionSummary,
  SpanDetail,
  TimelineResponse,
} from "@/types/api";

const API = "/api/v1";

export function useSessions() {
  return useQuery({
    queryKey: ["sessions"],
    queryFn: () => apiGet<SessionList>(`${API}/sessions`),
  });
}

export function useSession(id: string | undefined) {
  return useQuery({
    queryKey: ["session", id],
    queryFn: () => apiGet<SessionSummary>(`${API}/sessions/${id}`),
    enabled: !!id,
  });
}

export function useGraph(id: string | undefined) {
  return useQuery({
    queryKey: ["graph", id],
    queryFn: () => apiGet<GraphResponse>(`${API}/sessions/${id}/graph`),
    enabled: !!id,
  });
}

export function useTimeline(id: string | undefined) {
  return useQuery({
    queryKey: ["timeline", id],
    queryFn: () => apiGet<TimelineResponse>(`${API}/sessions/${id}/timeline`),
    enabled: !!id,
  });
}

export function useCost(id: string | undefined) {
  return useQuery({
    queryKey: ["cost", id],
    queryFn: () => apiGet<CostReport>(`${API}/sessions/${id}/cost`),
    enabled: !!id,
  });
}

export function useDiagram(id: string | undefined, type: string) {
  return useQuery({
    queryKey: ["diagram", id, type],
    queryFn: () => apiGet<DiagramResponse>(`${API}/sessions/${id}/diagram?type=${type}`),
    enabled: !!id,
  });
}

export function useSpan(id: string | undefined) {
  return useQuery({
    queryKey: ["span", id],
    queryFn: () => apiGet<SpanDetail>(`${API}/spans/${id}`),
    enabled: !!id,
  });
}

export function useCompare(a: string | undefined, b: string | undefined) {
  return useQuery({
    queryKey: ["compare", a, b],
    queryFn: () => apiGet<CompareReport>(`${API}/compare?a=${a}&b=${b}`),
    enabled: !!a && !!b,
  });
}
