import { Navigate, Outlet } from 'react-router-dom';
import { isLoggedIn } from '../api/auth';

export function ProtectedRoute() {
  return isLoggedIn() ? <Outlet /> : <Navigate to="/login" replace />;
}

