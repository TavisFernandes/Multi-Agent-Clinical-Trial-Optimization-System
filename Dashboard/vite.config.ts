import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/dashboard/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/ws": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        ws: true,
      },
      "/analyze": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
}));
