import { Route, Routes } from "react-router-dom";
import { CatalogPage } from "./pages/CatalogPage";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import "./styles.css";

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<CatalogPage />} />
        <Route path="/skills/:id" element={<SkillDetailPage />} />
      </Routes>
    </div>
  );
}
