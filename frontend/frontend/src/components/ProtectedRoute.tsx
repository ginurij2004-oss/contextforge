import {
  Navigate,
} from "react-router";

import {
  useAuth,
} from "../context/AuthContext";


export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode;
}) {
  const {
    user,
    loading,
  } = useAuth();


  if (loading) {
    return (
      <p>
        Loading...
      </p>
    );
  }


  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  return children;
}