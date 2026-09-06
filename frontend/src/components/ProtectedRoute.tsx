import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const ProtectedRoute: React.FC = () => {
  const { user, token, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyan-400 mb-2"></div>
        <span className="text-xs font-mono ml-3">Restoring credentials...</span>
      </div>
    );
  }

  // If no token or no user, redirect immediately to login and save attempted location
  if (!token || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
