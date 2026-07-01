/*
 * FILE: frontend/vite.config.ts
 *
 * WHAT THIS DOES:
 * Vite build configuration for the React app. Sets the dev server port to 5173
 * (the origin the backend allows in development).
 *
 * CHANGES THIS SESSION:
 * - Created with the React plugin and dev server port.
 *
 * WHERE IT FITS:
 * Controls how the frontend is served locally and built for Vercel.
 *
 * CALLED BY / IMPORTS FROM:
 * Read by the `vite` and `vite build` commands.
 */
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
