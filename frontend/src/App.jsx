import { Routes, Route } from "react-router-dom";
import OverviewPage from "./pages/OverviewPage";
import CustomerRiskExplorerPage from "./pages/CustomerRiskExplorerPage";
import ModelDiagnosticsPage from "./pages/ModelDiagnosticsPage";
import CustomerDetailPage from "./pages/CustomerDetailPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/explorer" element={<CustomerRiskExplorerPage />} />
      <Route path="/diagnostics" element={<ModelDiagnosticsPage />} />
      <Route path="/customer/:id" element={<CustomerDetailPage />} />
    </Routes>
  );
}
