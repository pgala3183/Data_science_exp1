import { Route, Routes } from "react-router-dom";
import { BayesPage } from "./pages/BayesPage";
import { BiasVariancePage } from "./pages/BiasVariancePage";
import { CltPage } from "./pages/CltPage";
import { GradientDescentPage } from "./pages/GradientDescentPage";
import { LandingPage } from "./pages/LandingPage";
import { RocPage } from "./pages/RocPage";
import "./styles.css";

export default function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/bayes" element={<BayesPage />} />
        <Route path="/clt" element={<CltPage />} />
        <Route path="/gradient-descent" element={<GradientDescentPage />} />
        <Route path="/bias-variance" element={<BiasVariancePage />} />
        <Route path="/roc" element={<RocPage />} />
      </Routes>
    </div>
  );
}
