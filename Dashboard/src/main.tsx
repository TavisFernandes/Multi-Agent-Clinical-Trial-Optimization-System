import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

document.documentElement.style.setProperty(
  "--robot-bg-url",
  `url("${import.meta.env.BASE_URL}robot.png")`,
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
