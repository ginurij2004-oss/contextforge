import {
  Navigate,
  Route,
  Routes,
} from "react-router";

import {
  useEffect,
} from "react";

import {
  useLocation,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";

import ProtectedRoute
  from "./components/ProtectedRoute";

import {
  useAuth,
} from "./context/AuthContext";

import Documents
  from "./pages/Documents";

import Analytics 
  from "./pages/Analytics";

import ActionCenter
  from "./pages/ActionCenter";

import Automations
  from "./pages/Automations";

import Operations
  from "./pages/Operations";

import AICompanion
  from "./components/AICompanion";

import "./components/AICompanion.css";
import "./brand/ContextForgeBranding.css";


function App() {
  const location =
    useLocation();

  const {
    user,
    loading,
  } = useAuth();


  useEffect(() => {

    document.title =
      "ContextForge";

    let iconLink =
      document.querySelector(
        'link[rel~="icon"]'
      ) as HTMLLinkElement | null;


    if (!iconLink) {

      iconLink =
        document.createElement(
          "link"
        );

      iconLink.rel =
        "icon";

      document.head.appendChild(
        iconLink
      );

    }


    iconLink.type =
      "image/png";

    iconLink.href =
      "/favicon.png";

  }, []);


  if (loading) {
    return (
      <p>
        Loading ContextForge...
      </p>
    );
  }


  return (
    <>
      {
        location.pathname === "/login"
        && (
          <AICompanion
            variant="login"
            label="ContextForge AI"
          />
        )
      }

      <Routes>
      <Route
        path="/"
        element={
          <Navigate
            to={
              user
                ? "/dashboard"
                : "/login"
            }
            replace
          />
        }
      />

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
  path="/documents"
  element={
    <ProtectedRoute>
      <Documents />
    </ProtectedRoute>
  }
/>

<Route
  path="/analytics"
  element={
    <ProtectedRoute>
      <Analytics />
    </ProtectedRoute>
  }
/>

<Route
  path="/actions"
  element={
    <ProtectedRoute>
      <ActionCenter />
    </ProtectedRoute>
  }
/>

<Route
  path="/automations"
  element={
    <ProtectedRoute>
      <Automations />
    </ProtectedRoute>
  }
/>

<Route
  path="/operations"
  element={
    <ProtectedRoute>
      <Operations />
    </ProtectedRoute>
  }
/>
      </Routes>
    </>
  );
}


export default App;