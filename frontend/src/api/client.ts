// Thin fetch wrapper with two modes:
//
// - Live (default): BASE is empty and paths hit the FastAPI backend — same-origin
//   in production, Vite's dev proxy in development.
// - Static demo (VITE_STATIC_API=1, used for the GitHub Pages build): every GET is
//   rewritten to a pre-baked JSON snapshot produced by
//   backend/app/export/static_api.py. Query strings become dotted suffixes
//   ("/diagram?type=flowchart" -> "/diagram.flowchart.json"), and paths are resolved
//   under Vite's BASE_URL so the demo works from a subpath like /agentic-viewer/demo/.
//   The two mappings must stay in lockstep with the exporter.

const STATIC = import.meta.env.VITE_STATIC_API === "1";

function toStaticPath(path: string): string {
  const [pathname, query] = path.split("?");
  let suffix = "";
  if (query) {
    const params = new URLSearchParams(query);
    suffix = [...params.values()].map((v) => `.${v}`).join("");
  }
  return `${import.meta.env.BASE_URL}${pathname.replace(/^\//, "")}${suffix}.json`;
}

export async function apiGet<T>(path: string): Promise<T> {
  const url = STATIC ? toStaticPath(path) : path;
  const res = await fetch(url, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`GET ${path} failed (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  if (STATIC) {
    throw new Error("This is a read-only static demo — ingestion needs the real backend.");
  }
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`POST ${path} failed (${res.status}): ${detail}`);
  }
  return res.json() as Promise<T>;
}
