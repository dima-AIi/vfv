import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layout/AppLayout'
import AuditPage from './pages/AuditPage'
import CrmPage from './pages/CrmPage'
import CustomerDetailPage from './pages/CustomerDetailPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectWorkspacePage from './pages/ProjectWorkspacePage'
import AIWorkspacePage from './pages/AIWorkspacePage'
import NotificationsPage from './pages/NotificationsPage'
import RegisterPage from './pages/RegisterPage'
import SettingsPage from './pages/SettingsPage'
import UsersPage from './pages/UsersPage'
import { AnonymousOnly, RequireAuth } from './features/auth/guards'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <AnonymousOnly>
              <LoginPage />
            </AnonymousOnly>
          }
        />
        <Route
          path="/register"
          element={
            <AnonymousOnly>
              <RegisterPage />
            </AnonymousOnly>
          }
        />
        <Route
          element={
            <RequireAuth>
              <AppLayout title="DevOS" />
            </RequireAuth>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectWorkspacePage />} />
          <Route path="/crm" element={<CrmPage />} />
          <Route path="/crm/:customerId" element={<CustomerDetailPage />} />
          <Route path="/ai" element={<AIWorkspacePage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
