import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import DeletionRequests from './pages/DeletionRequests';
import RequestDetails from './pages/RequestDetails';
import EvidenceExplorer from './pages/EvidenceExplorer';
import Remediation from './pages/Remediation';
import Evaluation from './pages/Evaluation';
import Settings from './pages/Settings';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main-content">
          <Navbar />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/requests" element={<DeletionRequests />} />
            <Route path="/requests/:caseId" element={<RequestDetails />} />
            <Route path="/evidence" element={<EvidenceExplorer />} />
            <Route path="/remediation" element={<Remediation />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
