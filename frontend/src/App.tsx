import 'antd/dist/reset.css';
import './styles/app.css';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { LogsPage } from './pages/LogsPage';
import { ResumeDetailPage } from './pages/ResumeDetailPage';
import { SemanticSearchPage } from './pages/SemanticSearchPage';
import { TaskListPage } from './pages/TaskListPage';
import { GroupReportPage } from './pages/GroupReportPage';
import { UploadPage } from './pages/UploadPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/tasks" element={<TaskListPage />} />
          <Route path="/semantic-search" element={<SemanticSearchPage />} />
          <Route path="/reports/group" element={<GroupReportPage />} />
          <Route path="/resumes/:id" element={<ResumeDetailPage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
