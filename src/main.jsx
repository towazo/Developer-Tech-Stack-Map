import { createRoot } from "react-dom/client";
import "bulma/css/bulma.min.css";
import "./styles/app.css";
import App from "./App";

createRoot(document.querySelector("#content")).render(<App />);
