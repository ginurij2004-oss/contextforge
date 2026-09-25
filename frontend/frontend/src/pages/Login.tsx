import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import {
  loginUser,
} from "../services/auth";

import "./Login.css";


export default function Login() {

  const navigate =
    useNavigate();


  const {
    theme,
    setTheme,
  } = useTheme();


  const {
    refreshUser,
  } = useAuth();


  const [
    email,
    setEmail,
  ] = useState("");


  const [
    password,
    setPassword,
  ] = useState("");


  const [
    showPassword,
    setShowPassword,
  ] = useState(false);


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  // ======================================================
  // Login Submit
  // ======================================================

  const handleSubmit =
    async (
      event:
        FormEvent<HTMLFormElement>
    ) => {

      event.preventDefault();


      // --------------------------------------------------
      // Basic validation
      // --------------------------------------------------

      if (
        !email.trim()
        || !password.trim()
      ) {

        setError(
          "Please enter your email and password."
        );

        return;
      }


      try {

        setLoading(
          true
        );

        setError("");


        // ==================================================
        // Login
        // ==================================================

        const response =
          await loginUser(
            email,
            password
          );


        // ==================================================
        // Save Access Token
        // ==================================================

        if (
          !response.access_token
        ) {

          throw new Error(
            "Login response did not include an access token."
          );
        }


        sessionStorage.setItem(
          "access_token",
          response.access_token
        );


        // ==================================================
        // Refresh AuthContext User
        // ==================================================

        await refreshUser();


        // ==================================================
        // Go to Dashboard
        // ==================================================

        navigate(
          "/"
        );


      } catch (error: any) {

        console.error(
          "LOGIN ERROR:",
          error
        );


        const detail =
          error?.response
            ?.data
            ?.detail
          ||
          error?.message
          ||
          "Invalid email or password.";


        setError(
          detail
        );


      } finally {

        setLoading(
          false
        );

      }

    };


  return (

    <div className="cf-page-shell login-page">


      {/* =================================================
          Top Bar
      ================================================= */}

      <div className="login-topbar">


        {/* Brand */}

        <div className="login-brand">

          <div className="login-brand-icon">

            C

          </div>


          <div className="login-brand-copy">

            <strong>
              ContextForge
            </strong>

            <span>
              Enterprise AI Workspace
            </span>

          </div>

        </div>


        {/* Theme Toggle */}

        <div className="cf-theme-toggle">


          <button
            type="button"

            className={
              theme === "dark"
              ? "active"
              : ""
            }

            onClick={() =>
              setTheme(
                "dark"
              )
            }
          >

            Dark

          </button>


          <button
            type="button"

            className={
              theme === "light"
              ? "active"
              : ""
            }

            onClick={() =>
              setTheme(
                "light"
              )
            }
          >

            Light

          </button>


        </div>


      </div>


      {/* =================================================
          Main Layout
      ================================================= */}

      <div className="login-layout">


        {/* =================================================
            Left Hero
        ================================================= */}

        <section className="login-hero">


          <div className="login-hero-badge">

            AI Workspace

          </div>


          <h1>

            Smarter knowledge.

            <br />

            Brighter possibilities.

          </h1>


          <p>

            Securely search your documents,
            chat with your knowledge base,
            and let AI assist your team with
            faster answers and structured actions.

          </p>


          {/* ===============================================
              Features
          =============================================== */}

          <div className="login-feature-list">


            {/* Feature 1 */}

            <div className="login-feature-item">

              <span className="feature-icon">

                ✦

              </span>


              <div>

                <strong>

                  Search across documents

                </strong>


                <p>

                  Ask questions and get grounded
                  answers with source-backed
                  responses.

                </p>

              </div>

            </div>


            {/* Feature 2 */}

            <div className="login-feature-item">

              <span className="feature-icon">

                ⚡

              </span>


              <div>

                <strong>

                  Agent-powered workflows

                </strong>


                <p>

                  Generate structured actions,
                  summaries and document-driven
                  insights.

                </p>

              </div>

            </div>


            {/* Feature 3 */}

            <div className="login-feature-item">

              <span className="feature-icon">

                ◫

              </span>


              <div>

                <strong>

                  Built for teams

                </strong>


                <p>

                  Minimal, elegant and fast —
                  designed for real business use.

                </p>

              </div>

            </div>


          </div>


        </section>


        {/* =================================================
            Right Login Form
        ================================================= */}

        <section className="login-form-area">


          <div className="login-card cf-glass">


            {/* Header */}

            <div className="login-card-header">

              <h2>

                Welcome back

              </h2>


              <p>

                Sign in to your
                ContextForge workspace

              </p>

            </div>


            {/* =================================================
                Form
            ================================================= */}

            <form
              onSubmit={
                handleSubmit
              }

              className="login-form"
            >


              {/* =============================================
                  Email
              ============================================= */}

              <div className="login-field">


                <label htmlFor="email">

                  Email address

                </label>


                <div className="input-shell">


                  <span className="input-icon">

                    ✉

                  </span>


                  <input
                    id="email"

                    type="email"

                    autoComplete="email"

                    placeholder="you@example.com"

                    value={
                      email
                    }

                    onChange={
                      (
                        event
                      ) =>
                        setEmail(
                          event.target.value
                        )
                    }

                    disabled={
                      loading
                    }
                  />


                </div>


              </div>


              {/* =============================================
                  Password
              ============================================= */}

              <div className="login-field">


                <div className="password-header">


                  <label htmlFor="password">

                    Password

                  </label>


                  <button
                    type="button"

                    className="text-button"
                  >

                    Forgot password?

                  </button>


                </div>


                <div className="input-shell">


                  <span className="input-icon">

                    ◌

                  </span>


                  <input
                    id="password"

                    type={
                      showPassword
                      ? "text"
                      : "password"
                    }

                    autoComplete="current-password"

                    placeholder="Enter your password"

                    value={
                      password
                    }

                    onChange={
                      (
                        event
                      ) =>
                        setPassword(
                          event.target.value
                        )
                    }

                    disabled={
                      loading
                    }
                  />


                  <button
                    type="button"

                    className="password-toggle"

                    onClick={() =>
                      setShowPassword(
                        (
                          previous
                        ) =>
                          !previous
                      )
                    }
                  >

                    {
                      showPassword
                      ? "Hide"
                      : "Show"
                    }

                  </button>


                </div>


              </div>


              {/* =============================================
                  Remember Me
              ============================================= */}

              <div className="login-row">


                <label className="remember-me">


                  <input
                    type="checkbox"
                  />


                  <span>

                    Remember me

                  </span>


                </label>


              </div>


              {/* =============================================
                  Error
              ============================================= */}

              {
                error
                && (

                  <div className="login-error">

                    {
                      error
                    }

                  </div>

                )
              }


              {/* =============================================
                  Submit
              ============================================= */}

              <button
                type="submit"

                className="login-submit"

                disabled={
                  loading
                }
              >

                {
                  loading
                  ? "Signing in..."
                  : "Sign in"
                }

              </button>


            </form>


            {/* =================================================
                Register Link
            ================================================= */}

            <div className="login-footer">


              <span>

                Don’t have an account?

              </span>


              <Link to="/register">

                Create one

              </Link>


            </div>


          </div>


        </section>


      </div>


      {/* =================================================
          Animated Decorative Bubbles
      ================================================= */}

      <div className="bubble bubble-1" />

      <div className="bubble bubble-2" />

      <div className="bubble bubble-3" />

      <div className="bubble bubble-4" />

      <div className="bubble bubble-5" />

      <div className="bubble bubble-6" />


    </div>

  );

}