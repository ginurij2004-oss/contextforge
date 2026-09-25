import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getCurrentUser,
  logoutUser,
  type AuthUser,
} from "../services/auth";


// ==========================================================
// Auth Context Type
// ==========================================================

interface AuthContextType {
  user: AuthUser | null;

  loading: boolean;

  isAuthenticated: boolean;

  refreshUser: () => Promise<void>;

  logout: () => void;
}


// ==========================================================
// Context
// ==========================================================

const AuthContext =
  createContext<AuthContextType | undefined>(
    undefined
  );


// ==========================================================
// Auth Provider
// ==========================================================

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {

  const [
    user,
    setUser,
  ] = useState<AuthUser | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  // ========================================================
  // Load Current User
  // ========================================================

  const refreshUser =
    async () => {

      const token =
        sessionStorage.getItem(
          "access_token"
        );


      // ----------------------------------------------------
      // No token = user is not logged in
      // ----------------------------------------------------

      if (!token) {

        setUser(
          null
        );

        setLoading(
          false
        );

        return;

      }


      try {

        const currentUser =
          await getCurrentUser();


        setUser(
          currentUser
        );


      } catch (error) {

        console.error(
          "AUTH USER ERROR:",
          error
        );


        // --------------------------------------------------
        // Token may be invalid / expired
        // --------------------------------------------------

        sessionStorage.removeItem(
          "access_token"
        );


        setUser(
          null
        );


      } finally {

        setLoading(
          false
        );

      }

    };


  // ========================================================
  // Initial Authentication Check
  // ========================================================

  useEffect(() => {

    refreshUser();

  }, []);


  // ========================================================
  // Logout
  // ========================================================

  const logout =
    () => {

      logoutUser();

      setUser(
        null
      );

    };


  // ========================================================
  // Authentication State
  // ========================================================

  const isAuthenticated =
    Boolean(
      user
    );


  // ========================================================
  // Context Value
  // ========================================================

  const value =
    useMemo(
      () => ({
        user,
        loading,
        isAuthenticated,
        refreshUser,
        logout,
      }),
      [
        user,
        loading,
        isAuthenticated,
      ]
    );


  // ========================================================
  // Provider
  // ========================================================

  return (

    <AuthContext.Provider
      value={
        value
      }
    >

      {
        children
      }

    </AuthContext.Provider>

  );

}


// ==========================================================
// useAuth Hook
// ==========================================================

export function useAuth() {

  const context =
    useContext(
      AuthContext
    );


  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );

  }


  return context;

}