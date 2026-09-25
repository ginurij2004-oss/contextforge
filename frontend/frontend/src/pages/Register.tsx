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
  registerUser,
} from "../services/auth";

import "./Register.css";


export default function Register() {

  const navigate =
    useNavigate();

  const {
    theme,
    setTheme,
  } = useTheme();


  const [
    email,
    setEmail,
  ] = useState("");


  const [
    password,
    setPassword,
  ] = useState("");


  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");


  const [
    showPassword,
    setShowPassword,
  ] = useState(false);


  const [
    showConfirmPassword,
    setShowConfirmPassword,
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
  // Password Strength
  // ======================================================

  const passwordStrength =
    getPasswordStrength(
      password
    );


  // ======================================================
  // Submit
  // ======================================================

  const handleSubmit =
    async (
      event: FormEvent<HTMLFormElement>
    ) => {

      event.preventDefault();


      setError("");


      // --------------------------------------------------
      // Validation
      // --------------------------------------------------

      if (
        !email.trim()
        || !password.trim()
        || !confirmPassword.trim()
      ) {

        setError(
          "Please complete all required fields."
        );

        return;

      }


      if (
        password.length < 8
      ) {

        setError(
          "Password must contain at least 8 characters."
        );

        return;

      }


      if (
        password !== confirmPassword
      ) {

        setError(
          "Passwords do not match."
        );

        return;

      }


      try {

        setLoading(true);


        await registerUser(
          email,
          password
        );


        // --------------------------------------------------
        // Registration successful
        // --------------------------------------------------

        navigate(
          "/login",
          {
            state: {
              registered: true,
            },
          }
        );


      } catch (error: any) {

        console.error(
          "REGISTER ERROR:",
          error
        );


        const detail =
          error?.response
            ?.data
            ?.detail;


        setError(
          detail
          || "Registration failed. Please try again."
        );


      } finally {

        setLoading(false);

      }

    };


  return (

    <div className="cf-page-shell register-page">


      {/* =================================================
          Top Bar
      ================================================= */}

      <div className="register-topbar">


        {/* Brand */}

        <div className="register-brand">

          <div className="register-brand-icon">

            C

          </div>


          <div className="register-brand-copy">

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
          Main
      ================================================= */}

      <div className="register-layout">


        {/* =================================================
            Left Hero
        ================================================= */}

        <section className="register-hero">


          <div className="register-hero-badge">

            Build your AI workspace

          </div>


          <h1>

            Your knowledge.
            <br />

            <span>
              Supercharged by AI.
            </span>

          </h1>


          <p>

            Create your ContextForge workspace
            and turn documents into searchable,
            intelligent knowledge.

          </p>


          {/* Features */}

          <div className="register-feature-grid">


            <div className="register-feature-card">

              <span className="register-feature-icon">

                ◫

              </span>


              <div>

                <strong>
                  Upload your knowledge
                </strong>

                <p>
                  Turn PDFs into searchable
                  AI-ready knowledge.
                </p>

              </div>

            </div>


            <div className="register-feature-card">

              <span className="register-feature-icon">

                ✦

              </span>


              <div>

                <strong>
                  Ask grounded questions
                </strong>

                <p>
                  Receive answers backed by
                  your own documents.
                </p>

              </div>

            </div>


            <div className="register-feature-card">

              <span className="register-feature-icon">

                ⚡

              </span>


              <div>

                <strong>
                  Use intelligent agents
                </strong>

                <p>
                  Analyze information and
                  generate structured actions.
                </p>

              </div>

            </div>


            <div className="register-feature-card">

              <span className="register-feature-icon">

                ◈

              </span>


              <div>

                <strong>
                  Measure performance
                </strong>

                <p>
                  Monitor RAG quality,
                  latency and AI usage.
                </p>

              </div>

            </div>


          </div>


          {/* Quote */}

          <div className="register-quote">

            <div className="register-quote-line" />

            <p>

              Turn information into
              intelligence.

            </p>

            <span>
              ContextForge
            </span>

          </div>


        </section>


        {/* =================================================
            Registration Form
        ================================================= */}

        <section className="register-form-area">


          <div className="register-card cf-glass">


            {/* Header */}

            <div className="register-card-header">

              <div className="register-card-icon">

                C

              </div>


              <h2>

                Create your account

              </h2>


              <p>

                Start building your intelligent
                knowledge workspace.

              </p>

            </div>


            {/* Form */}

            <form
              className="register-form"

              onSubmit={
                handleSubmit
              }
            >


              {/* Email */}

              <div className="register-field">

                <label
                  htmlFor="register-email"
                >

                  Email address

                </label>


                <div className="register-input-shell">

                  <span className="register-input-icon">

                    ✉

                  </span>


                  <input
                    id="register-email"

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
                  />

                </div>

              </div>


              {/* Password */}

              <div className="register-field">


                <label
                  htmlFor="register-password"
                >

                  Password

                </label>


                <div className="register-input-shell">


                  <span className="register-input-icon">

                    ◌

                  </span>


                  <input
                    id="register-password"

                    type={
                      showPassword
                      ? "text"
                      : "password"
                    }

                    autoComplete="new-password"

                    placeholder="Create a password"

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
                  />


                  <button
                    type="button"

                    className="register-password-toggle"

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


                {/* Password Strength */}

                {
                  password
                  && (

                    <PasswordStrength
                      strength={
                        passwordStrength
                      }
                    />

                  )
                }


              </div>


              {/* Confirm Password */}

              <div className="register-field">


                <label
                  htmlFor="confirm-password"
                >

                  Confirm password

                </label>


                <div className="register-input-shell">


                  <span className="register-input-icon">

                    ✓

                  </span>


                  <input
                    id="confirm-password"

                    type={
                      showConfirmPassword
                      ? "text"
                      : "password"
                    }

                    autoComplete="new-password"

                    placeholder="Repeat your password"

                    value={
                      confirmPassword
                    }

                    onChange={
                      (
                        event
                      ) =>
                        setConfirmPassword(
                          event.target.value
                        )
                    }
                  />


                  <button
                    type="button"

                    className="register-password-toggle"

                    onClick={() =>
                      setShowConfirmPassword(
                        (
                          previous
                        ) =>
                          !previous
                      )
                    }
                  >

                    {
                      showConfirmPassword
                      ? "Hide"
                      : "Show"
                    }

                  </button>


                </div>


                {
                  confirmPassword

                  &&

                  password
                  !== confirmPassword

                  && (

                    <span className="password-mismatch">

                      Passwords do not match.

                    </span>

                  )
                }


              </div>


              {/* Agreement */}

              <label className="register-agreement">

                <input
                  type="checkbox"
                  required
                />

                <span>

                  I agree to the{" "}

                  <button
                    type="button"
                    className="register-inline-link"
                  >
                    Terms
                  </button>

                  {" "}and{" "}

                  <button
                    type="button"
                    className="register-inline-link"
                  >
                    Privacy Policy
                  </button>

                  .

                </span>

              </label>


              {/* Error */}

              {
                error
                && (

                  <div className="register-error">

                    <span>
                      !
                    </span>

                    {
                      error
                    }

                  </div>

                )
              }


              {/* Submit */}

              <button
                type="submit"

                className="register-submit"

                disabled={
                  loading
                }
              >

                {
                  loading
                  ? "Creating account..."
                  : "Create account"
                }

              </button>


            </form>


            {/* Login Link */}

            <div className="register-footer">

              <span>
                Already have an account?
              </span>


              <Link to="/login">

                Sign in

              </Link>

            </div>


          </div>


        </section>


      </div>


      {/* =================================================
          Animated Background Bubbles
      ================================================= */}

      <div className="register-bubble register-bubble-1" />

      <div className="register-bubble register-bubble-2" />

      <div className="register-bubble register-bubble-3" />

      <div className="register-bubble register-bubble-4" />

      <div className="register-bubble register-bubble-5" />

      <div className="register-bubble register-bubble-6" />


    </div>

  );

}


// ==========================================================
// Password Strength Component
// ==========================================================

function PasswordStrength({
  strength,
}: {
  strength: PasswordStrengthValue;
}) {

  return (

    <div className="password-strength">


      <div className="password-strength-bars">


        {
          [1, 2, 3, 4].map(
            (
              level
            ) => (

              <span
                key={
                  level
                }

                className={
                  (
                    level
                    <= strength.score

                    ? (
                      `active ${strength.className}`
                    )

                    : ""
                  )
                }
              />

            )
          )
        }


      </div>


      <span
        className={
          (
            "password-strength-label "
            + strength.className
          )
        }
      >

        {
          strength.label
        }

      </span>


    </div>

  );

}


// ==========================================================
// Password Strength
// ==========================================================

type PasswordStrengthValue = {
  score: number;
  label: string;
  className: string;
};


function getPasswordStrength(
  password: string
): PasswordStrengthValue {

  let score = 0;


  if (
    password.length >= 8
  ) {

    score += 1;

  }


  if (
    /[A-Z]/.test(
      password
    )

    &&

    /[a-z]/.test(
      password
    )
  ) {

    score += 1;

  }


  if (
    /\d/.test(
      password
    )
  ) {

    score += 1;

  }


  if (
    /[^A-Za-z0-9]/.test(
      password
    )
  ) {

    score += 1;

  }


  if (
    score <= 1
  ) {

    return {
      score: Math.max(
        score,
        1
      ),
      label: "Weak",
      className: "weak",
    };

  }


  if (
    score === 2
  ) {

    return {
      score,
      label: "Fair",
      className: "fair",
    };

  }


  if (
    score === 3
  ) {

    return {
      score,
      label: "Good",
      className: "good",
    };

  }


  return {
    score: 4,
    label: "Strong",
    className: "strong",
  };

}