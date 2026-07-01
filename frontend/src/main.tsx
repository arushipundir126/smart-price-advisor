/*
 * FILE: frontend/src/main.tsx
 *
 * WHAT THIS DOES:
 * Boots the React app: mounts <App /> into #root and loads the design tokens.
 *
 * CHANGES THIS SESSION:
 * - Created the React entry point.
 *
 * WHERE IT FITS:
 * The first code the browser runs after index.html.
 *
 * CALLED BY / IMPORTS FROM:
 * Imports App and index.css. Referenced by index.html.
 */
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
