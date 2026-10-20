import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// VITE_BASE lets the GitHub Pages workflow serve the demo from a subpath
// (e.g. /agentic-viewer/demo/) without changing local dev or Vercel builds.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to the FastAPI backend during development.
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/healthz": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
