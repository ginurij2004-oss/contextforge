import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  approveAction,
  executeAction,
  getActions,
  rejectAction,
  retryAction,
  updateAction,
  type ActionRequestItem,
  type ActionStatus,
} from "../services/actions";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import "./Dashboard.css";
import "./ActionCenter.css";


type ActionFilter =
  | "all"
  | "pending"
  | "approved"
  | "completed"
  | "failed"
  | "rejected";


function formatDate(
  value: string | null
) {

  if (!value) {
    return "—";
  }


  const date =
    new Date(value);


  if (
    Number.isNaN(
      date.getTime()
    )
  ) {

    return value;

  }


  return date.toLocaleString();
}


function textPayloadValue(
  action: ActionRequestItem,
  key: string
) {

  const value =
    action.payload[key];


  if (
    value === null
    || value === undefined
  ) {

    return "";

  }


  return String(value);
}


function statusLabel(
  status: ActionStatus
) {

  return (
    status.charAt(0).toUpperCase()
    + status.slice(1)
  );
}


function actionIcon(
  actionType: string
) {

  switch (actionType) {

    case "email":
      return "✉";

    case "calendar":
      return "▦";

    case "reminder":
      return "◷";

    case "webhook":
      return "↗";

    case "notification":
      return "◉";

    default:
      return "⚡";

  }

}


export default function ActionCenter() {

  const navigate =
    useNavigate();


  const {
    theme,
    setTheme,
  } = useTheme();


  const {
    logout,
  } = useAuth();


  const [
    actions,
    setActions,
  ] = useState<ActionRequestItem[]>(
    []
  );


  const [
    filter,
    setFilter,
  ] = useState<ActionFilter>(
    "all"
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    refreshing,
    setRefreshing,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);


  const [
    busyActionId,
    setBusyActionId,
  ] = useState<number | null>(
    null
  );


  const [
    editingAction,
    setEditingAction,
  ] = useState<ActionRequestItem | null>(
    null
  );


  const [
    editTitle,
    setEditTitle,
  ] = useState("");


  const [
    editEmailTo,
    setEditEmailTo,
  ] = useState("");


  const [
    editEmailSubject,
    setEditEmailSubject,
  ] = useState("");


  const [
    editEmailBody,
    setEditEmailBody,
  ] = useState("");


  const [
    editCalendarTitle,
    setEditCalendarTitle,
  ] = useState("");

  const [
    editCalendarStart,
    setEditCalendarStart,
  ] = useState("");

  const [
    editCalendarEnd,
    setEditCalendarEnd,
  ] = useState("");

  const [
    editCalendarDescription,
    setEditCalendarDescription,
  ] = useState("");

  const [
    editCalendarTimezone,
    setEditCalendarTimezone,
  ] = useState(
    "Asia/Colombo"
  );


  const [
    editWebhookDataJson,
    setEditWebhookDataJson,
  ] = useState("{}");


  // ======================================================
  // Load
  // ======================================================

  useEffect(() => {

    loadActions();

  }, []);


  const loadActions =
    async (
      silent = false
    ) => {

      try {

        if (silent) {

          setRefreshing(
            true
          );

        } else {

          setLoading(
            true
          );

        }


        setError("");


        const data =
          await getActions();


        setActions(
          data
        );


      } catch (error: any) {

        console.error(
          "LOAD ACTIONS ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to load actions."
        );


      } finally {

        setLoading(
          false
        );

        setRefreshing(
          false
        );

      }

    };


  // ======================================================
  // Derived Data
  // ======================================================

  const counts =
    useMemo(
      () => {

        return {

          all:
            actions.length,

          pending:
            actions.filter(
              action =>
                action.status
                === "pending"
            ).length,

          approved:
            actions.filter(
              action =>
                action.status
                === "approved"
            ).length,

          completed:
            actions.filter(
              action =>
                action.status
                === "completed"
            ).length,

          failed:
            actions.filter(
              action =>
                action.status
                === "failed"
            ).length,

          rejected:
            actions.filter(
              action =>
                action.status
                === "rejected"
            ).length,

        };

      },
      [
        actions,
      ]
    );


  const visibleActions =
    useMemo(
      () => {

        if (
          filter === "all"
        ) {

          return actions;

        }


        return actions.filter(
          action =>
            action.status
            === filter
        );

      },
      [
        actions,
        filter,
      ]
    );


  // ======================================================
  // Update Local Action
  // ======================================================

  const replaceAction =
    (
      updated:
        ActionRequestItem
    ) => {

      setActions(
        previous =>
          previous.map(
            action =>
              action.id
              === updated.id

                ? updated
                : action
          )
      );

    };


  // ======================================================
  // Approve
  // ======================================================

  const handleApprove =
    async (
      actionId: number
    ) => {

      try {

        setBusyActionId(
          actionId
        );

        setError("");


        const updated =
          await approveAction(
            actionId
          );


        replaceAction(
          updated
        );


      } catch (error: any) {

        console.error(
          "APPROVE ACTION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to approve action."
        );


      } finally {

        setBusyActionId(
          null
        );

      }

    };


  // ======================================================
  // Execute Approved External Action
  // ======================================================

  const handleExecute =
    async (
      actionId: number
    ) => {

      try {

        setBusyActionId(
          actionId
        );

        setError("");


        const updated =
          await executeAction(
            actionId
          );


        replaceAction(
          updated
        );


        if (
          updated.status
          === "failed"
        ) {

          setError(
            updated.error_message
            || "Automation execution failed."
          );

        }


      } catch (error: any) {

        console.error(
          "EXECUTE ACTION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to execute action."
        );


        await loadActions(
          true
        );


      } finally {

        setBusyActionId(
          null
        );

      }

    };


  // ======================================================
  // Retry Failed Action
  // ======================================================

  const handleRetry =
    async (
      actionId: number
    ) => {

      const confirmed = window.confirm(
        "Retry this failed action? Verify the external service did not already apply the previous request before retrying."
      );

      if (!confirmed) {
        return;
      }

      try {
        setBusyActionId(actionId);
        setError("");

        await retryAction(actionId);
        await loadActions(true);

      } catch (error: any) {
        console.error(
          "RETRY ACTION ERROR:",
          error
        );

        setError(
          error?.response?.data?.detail
          || "Failed to retry action."
        );
      } finally {
        setBusyActionId(null);
      }
    };


  // ======================================================
  // Reject
  // ======================================================

  const handleReject =
    async (
      actionId: number
    ) => {

      try {

        setBusyActionId(
          actionId
        );

        setError("");


        const updated =
          await rejectAction(
            actionId
          );


        replaceAction(
          updated
        );


      } catch (error: any) {

        console.error(
          "REJECT ACTION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to reject action."
        );


      } finally {

        setBusyActionId(
          null
        );

      }

    };


  // ======================================================
  // Edit
  // ======================================================

  const startEdit =
    (
      action:
        ActionRequestItem
    ) => {

      setEditingAction(
        action
      );

      setEditTitle(
        action.title
      );


      if (
        action.action_type
        === "email"
      ) {

        setEditEmailTo(
          textPayloadValue(
            action,
            "to"
          )
        );

        setEditEmailSubject(
          textPayloadValue(
            action,
            "subject"
          )
        );

        setEditEmailBody(
          textPayloadValue(
            action,
            "body"
          )
        );

      } else {

        setEditEmailTo("");
        setEditEmailSubject("");
        setEditEmailBody("");

      }


      if (
        action.action_type
        === "calendar"
      ) {

        setEditCalendarTitle(
          textPayloadValue(
            action,
            "title"
          )
        );

        setEditCalendarStart(
          textPayloadValue(
            action,
            "start_time"
          )
        );

        setEditCalendarEnd(
          textPayloadValue(
            action,
            "end_time"
          )
        );

        setEditCalendarDescription(
          textPayloadValue(
            action,
            "description"
          )
        );

        setEditCalendarTimezone(
          textPayloadValue(
            action,
            "timezone"
          )
          || "Asia/Colombo"
        );

      } else {

        setEditCalendarTitle("");
        setEditCalendarStart("");
        setEditCalendarEnd("");
        setEditCalendarDescription("");
        setEditCalendarTimezone(
          "Asia/Colombo"
        );

      }


      if (
        action.action_type
        === "webhook"
      ) {

        const data =
          action.payload["data"];

        setEditWebhookDataJson(
          JSON.stringify(
            (
              data
              && typeof data
              === "object"
              && !Array.isArray(data)
            )
              ? data
              : {},
            null,
            2
          )
        );

      } else {

        setEditWebhookDataJson(
          "{}"
        );

      }

    };


  const closeEdit =
    () => {

      setEditingAction(
        null
      );

      setEditTitle("");
      setEditEmailTo("");
      setEditEmailSubject("");
      setEditEmailBody("");
      setEditCalendarTitle("");
      setEditCalendarStart("");
      setEditCalendarEnd("");
      setEditCalendarDescription("");
      setEditCalendarTimezone(
        "Asia/Colombo"
      );
      setEditWebhookDataJson(
        "{}"
      );

    };


  const saveEdit =
    async (
      event:
        FormEvent
    ) => {

      event.preventDefault();


      if (
        !editingAction
      ) {

        return;

      }


      const title =
        editTitle.trim();


      if (!title) {

        setError(
          "Action title is required."
        );

        return;

      }


      let payload =
        editingAction.payload;


      if (
        editingAction.action_type
        === "email"
      ) {

        const to =
          editEmailTo.trim();

        const subject =
          editEmailSubject.trim();

        const body =
          editEmailBody.trim();


        if (
          !to
          || !subject
          || !body
        ) {

          setError(
            "Recipient, subject and message are required."
          );

          return;

        }


        payload = {
          ...editingAction.payload,
          to,
          subject,
          body,
        };

      }


      if (
        editingAction.action_type
        === "calendar"
      ) {

        const eventTitle =
          editCalendarTitle.trim();

        const startTime =
          editCalendarStart.trim();

        const endTime =
          editCalendarEnd.trim();

        const description =
          editCalendarDescription.trim();

        const timezone =
          editCalendarTimezone.trim();


        if (
          !eventTitle
          || !startTime
          || !endTime
          || !timezone
        ) {

          setError(
            "Event title, start time, end time and timezone are required."
          );

          return;

        }


        payload = {
          ...editingAction.payload,
          title: eventTitle,
          start_time: startTime,
          end_time: endTime,
          description,
          timezone,
        };

      }


      if (
        editingAction.action_type
        === "webhook"
      ) {

        let parsedData:
          unknown;


        try {

          parsedData =
            JSON.parse(
              editWebhookDataJson
            );


        } catch {

          setError(
            "Webhook data must be valid JSON."
          );

          return;

        }


        if (
          !parsedData
          || typeof parsedData
          !== "object"
          || Array.isArray(
            parsedData
          )
        ) {

          setError(
            "Webhook data must be a JSON object."
          );

          return;

        }


        payload = {
          ...editingAction.payload,
          target: "demo_echo",
          data: parsedData,
        };

      }


      try {

        setBusyActionId(
          editingAction.id
        );

        setError("");


        const updated =
          await updateAction(
            editingAction.id,
            {
              title,
              payload,
            }
          );


        replaceAction(
          updated
        );


        closeEdit();


      } catch (error: any) {

        console.error(
          "UPDATE ACTION ERROR:",
          error
        );


        setError(
          error?.response
            ?.data
            ?.detail
          || "Failed to update action."
        );


      } finally {

        setBusyActionId(
          null
        );

      }

    };


  // ======================================================
  // Logout
  // ======================================================

  const handleLogout =
    () => {

      logout();

      navigate(
        "/login"
      );

    };


  // ======================================================
  // Loading
  // ======================================================

  if (
    loading
  ) {

    return (

      <div className="cf-dashboard-loading">

        <div className="cf-dashboard-loading-logo">
          C
        </div>

        <span>
          Loading Action Center...
        </span>

      </div>

    );

  }


  return (

    <div className="cf-dashboard cf-action-center">


      {
        mobileSidebarOpen
        && (

          <button
            type="button"

            className="cf-mobile-overlay"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          />

        )
      }


      {/* =================================================
          Sidebar
      ================================================= */}

      <aside
        className={
          mobileSidebarOpen

            ? "cf-sidebar cf-sidebar-open"

            : "cf-sidebar"
        }
      >

        <div className="cf-sidebar-brand">

          <div className="cf-sidebar-logo">
            C
          </div>


          <div className="cf-sidebar-brand-copy">

            <strong>
              ContextForge
            </strong>

            <span>
              Enterprise AI
            </span>

          </div>


          <button
            type="button"

            className="cf-sidebar-mobile-close"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          >
            ×
          </button>

        </div>


        <button
          type="button"

          className="cf-new-chat"

          onClick={() =>
            navigate(
              "/dashboard"
            )
          }
        >

          <span className="cf-new-chat-icon">
            ✦
          </span>

          Back to workspace

        </button>


        <nav className="cf-sidebar-nav">

          <button
            type="button"

            onClick={() =>
              navigate(
                "/dashboard"
              )
            }
          >

            <span className="cf-nav-icon">
              ✦
            </span>

            AI Workspace

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/documents"
              )
            }
          >

            <span className="cf-nav-icon">
              ◫
            </span>

            Documents

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/analytics"
              )
            }
          >

            <span className="cf-nav-icon">
              ◩
            </span>

            Analytics

          </button>


          <button
            type="button"
            className="active"
          >

            <span className="cf-nav-icon">
              ⚡
            </span>

            Action Center

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/automations"
              )
            }
          >

            <span className="cf-nav-icon">
              ⟳
            </span>

            Automations

          </button>


          <button
            type="button"

            onClick={() =>
              navigate(
                "/operations"
              )
            }
          >

            <span className="cf-nav-icon">
              ◎
            </span>

            Operations

          </button>

        </nav>


        <div className="cf-action-sidebar-summary">

          <span>
            Pending approval
          </span>

          <strong>
            {
              counts.pending
            }
          </strong>

          <p>
            External actions always wait
            for human approval.
          </p>

        </div>


        <div className="cf-sidebar-footer">

          <div className="cf-system-online">

            <span className="cf-online-dot" />

            ContextForge online

          </div>


          <button
            type="button"

            onClick={
              handleLogout
            }
          >

            <span className="cf-nav-icon">
              ↗
            </span>

            Sign out

          </button>

        </div>

      </aside>


      {/* =================================================
          Main
      ================================================= */}

      <main className="cf-workspace cf-action-workspace">

        <header className="cf-workspace-header cf-action-header">

          <div className="cf-header-left">

            <button
              type="button"

              className="cf-mobile-menu"

              onClick={() =>
                setMobileSidebarOpen(
                  true
                )
              }
            >
              ☰
            </button>


            <div>

              <span className="cf-header-eyebrow">
                Automation
              </span>

              <h1>
                Action Center
              </h1>

              <p>
                Review, edit and approve
                AI-proposed actions before execution.
              </p>

            </div>

          </div>


          <div className="cf-action-header-tools">

            <button
              type="button"

              className="cf-action-refresh"

              disabled={
                refreshing
              }

              onClick={() =>
                loadActions(
                  true
                )
              }
            >

              {
                refreshing
                  ? "Refreshing..."
                  : "↻ Refresh"
              }

            </button>


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

        </header>


        <section className="cf-action-content">

          {/* ===============================================
              Overview
          =============================================== */}

          <div className="cf-action-overview">

            <div className="cf-action-stat">

              <span>
                Total actions
              </span>

              <strong>
                {
                  counts.all
                }
              </strong>

              <small>
                All recorded requests
              </small>

            </div>


            <div className="cf-action-stat pending">

              <span>
                Pending
              </span>

              <strong>
                {
                  counts.pending
                }
              </strong>

              <small>
                Waiting for your decision
              </small>

            </div>


            <div className="cf-action-stat approved">

              <span>
                Approved
              </span>

              <strong>
                {
                  counts.approved
                }
              </strong>

              <small>
                Ready for execution
              </small>

            </div>


            <div className="cf-action-stat rejected">

              <span>
                Rejected
              </span>

              <strong>
                {
                  counts.rejected
                }
              </strong>

              <small>
                Blocked by human review
              </small>

            </div>

          </div>


          {/* ===============================================
              Toolbar
          =============================================== */}

          <div className="cf-action-list-toolbar">

            <div>

              <span className="cf-action-section-label">
                Approval queue
              </span>

              <h2>
                Actions
              </h2>

            </div>


            <div className="cf-action-filter-tabs">

              {
                (
                  [
                    "all",
                    "pending",
                    "approved",
                    "completed",
                    "failed",
                    "rejected",
                  ] as ActionFilter[]
                ).map(
                  item => (

                    <button
                      type="button"

                      key={
                        item
                      }

                      className={
                        filter === item
                          ? "active"
                          : ""
                      }

                      onClick={() =>
                        setFilter(
                          item
                        )
                      }
                    >

                      {
                        item.charAt(0)
                          .toUpperCase()
                        + item.slice(1)
                      }

                      <span>
                        {
                          counts[item]
                        }
                      </span>

                    </button>

                  )
                )
              }

            </div>

          </div>


          {
            error
            && (

              <div className="cf-action-error">

                <strong>
                  Action Center
                </strong>

                <span>
                  {
                    error
                  }
                </span>

              </div>

            )
          }


          {/* ===============================================
              Action Cards
          =============================================== */}

          {
            visibleActions.length
            === 0
            ? (

              <div className="cf-action-empty">

                <div className="cf-action-empty-icon">
                  ⚡
                </div>

                <h3>
                  No {
                    filter === "all"
                      ? ""
                      : `${filter} `
                  }actions
                </h3>

                <p>
                  Agent-generated executable actions
                  will appear here for review.
                </p>

              </div>

            )
            : (

              <div className="cf-action-list">

                {
                  visibleActions.map(
                    action => {

                      const isBusy =
                        busyActionId
                        === action.id;


                      return (

                        <article
                          className="cf-action-card"

                          key={
                            action.id
                          }
                        >

                          <div className="cf-action-card-top">

                            <div className="cf-action-type">

                              <div className="cf-action-type-icon">
                                {
                                  actionIcon(
                                    action.action_type
                                  )
                                }
                              </div>


                              <div>

                                <span>
                                  {
                                    action.action_type
                                      .toUpperCase()
                                  }
                                </span>

                                <strong>
                                  {
                                    action.title
                                  }
                                </strong>

                              </div>

                            </div>


                            <span
                              className={
                                (
                                  "cf-action-status "
                                  + action.status
                                )
                              }
                            >

                              {
                                statusLabel(
                                  action.status
                                )
                              }

                            </span>

                          </div>


                          {
                            action.action_type
                            === "email"
                            && (

                              <div className="cf-email-preview">

                                <div className="cf-email-row">

                                  <span>
                                    To
                                  </span>

                                  <strong>
                                    {
                                      textPayloadValue(
                                        action,
                                        "to"
                                      )
                                      || "No recipient"
                                    }
                                  </strong>

                                </div>


                                <div className="cf-email-row">

                                  <span>
                                    Subject
                                  </span>

                                  <strong>
                                    {
                                      textPayloadValue(
                                        action,
                                        "subject"
                                      )
                                      || "No subject"
                                    }
                                  </strong>

                                </div>


                                <div className="cf-email-body">

                                  {
                                    textPayloadValue(
                                      action,
                                      "body"
                                    )
                                    || "No message body"
                                  }

                                </div>

                              </div>

                            )
                          }


                          {
                            action.action_type
                            === "calendar"
                            && (

                              <div className="cf-email-preview">

                                <div className="cf-email-row">
                                  <span>
                                    Event
                                  </span>

                                  <strong>
                                    {
                                      textPayloadValue(
                                        action,
                                        "title"
                                      )
                                      || "Untitled event"
                                    }
                                  </strong>
                                </div>


                                <div className="cf-email-row">
                                  <span>
                                    Start
                                  </span>

                                  <strong>
                                    {
                                      formatDate(
                                        textPayloadValue(
                                          action,
                                          "start_time"
                                        )
                                      )
                                    }
                                  </strong>
                                </div>


                                <div className="cf-email-row">
                                  <span>
                                    End
                                  </span>

                                  <strong>
                                    {
                                      formatDate(
                                        textPayloadValue(
                                          action,
                                          "end_time"
                                        )
                                      )
                                    }
                                  </strong>
                                </div>


                                <div className="cf-email-row">
                                  <span>
                                    Timezone
                                  </span>

                                  <strong>
                                    {
                                      textPayloadValue(
                                        action,
                                        "timezone"
                                      )
                                      || "—"
                                    }
                                  </strong>
                                </div>


                                <div className="cf-email-body">
                                  {
                                    textPayloadValue(
                                      action,
                                      "description"
                                    )
                                    || "No event description"
                                  }
                                </div>

                              </div>

                            )
                          }


                          {
                            action.action_type
                            === "webhook"
                            && (

                              <div className="cf-email-preview">

                                <div className="cf-email-row">
                                  <span>
                                    Target
                                  </span>

                                  <strong>
                                    {
                                      textPayloadValue(
                                        action,
                                        "target"
                                      )
                                      || "—"
                                    }
                                  </strong>
                                </div>


                                <div className="cf-email-body">

                                  <pre className="cf-action-json">
                                    {
                                      JSON.stringify(
                                        action.payload["data"]
                                        || {},
                                        null,
                                        2
                                      )
                                    }
                                  </pre>

                                </div>

                              </div>

                            )
                          }


                          {
                            action.action_type
                            !== "email"
                            && action.action_type
                            !== "calendar"
                            && action.action_type
                            !== "webhook"
                            && (

                              <pre className="cf-action-json">

                                {
                                  JSON.stringify(
                                    action.payload,
                                    null,
                                    2
                                  )
                                }

                              </pre>

                            )
                          }


                          <div className="cf-action-card-meta">

                            <span>
                              ID #{action.id}
                            </span>

                            <span>
                              Created {
                                formatDate(
                                  action.created_at
                                )
                              }
                            </span>

                            {
                              action.message_id
                              && (

                                <span>
                                  Message #{action.message_id}
                                </span>

                              )
                            }

                          </div>


                          {
                            action.status
                            === "approved"
                            && (

                              <div className="cf-action-note approved">

                                ✓ Human approval recorded.
                                This action is ready for
                                explicit execution.

                              </div>

                            )
                          }


                          {
                            action.status
                            === "completed"
                            && (

                              <div className="cf-action-note approved">

                                {
                                  action.action_type
                                  === "calendar"
                                    ? "✓ Calendar event created successfully"
                                    : action.action_type
                                      === "webhook"
                                        ? "✓ Webhook action executed successfully"
                                        : "✓ Email sent successfully"
                                }
                                {
                                  action.executed_at
                                  ? ` on ${formatDate(
                                      action.executed_at
                                    )}`
                                  : "."
                                }

                              </div>

                            )
                          }


                          {
                            action.status
                            === "executing"
                            && (

                              <div className="cf-action-note approved">

                                {
                                  action.action_type
                                  === "calendar"
                                    ? "Calendar event creation is in progress."
                                    : action.action_type
                                      === "webhook"
                                        ? "Webhook execution is in progress."
                                        : "Email execution is in progress."
                                }

                              </div>

                            )
                          }


                          {
                            action.status
                            === "rejected"
                            && (

                              <div className="cf-action-note rejected">

                                This action was rejected
                                and cannot be edited.

                              </div>

                            )
                          }


                          {
                            action.status
                            === "failed"
                            && action.error_message
                            && (

                              <div className="cf-action-note rejected">

                                {
                                  action.error_message
                                }

                              </div>

                            )
                          }


                          {
                            action.status
                            === "failed"
                            && (

                              <div className="cf-action-card-actions">
                                <button
                                  type="button"
                                  className="secondary"
                                  disabled={isBusy}
                                  onClick={() =>
                                    handleRetry(action.id)
                                  }
                                >
                                  {
                                    isBusy
                                      ? "Creating retry..."
                                      : "Retry Failed Action"
                                  }
                                </button>
                              </div>

                            )
                          }


                          {
                            action.status
                            === "approved"
                            && (
                              action.action_type
                              === "email"
                              || action.action_type
                              === "calendar"
                              || action.action_type
                              === "webhook"
                            )
                            && (

                              <div className="cf-action-card-actions">

                                <button
                                  type="button"

                                  className="primary"

                                  disabled={
                                    isBusy
                                  }

                                  onClick={() =>
                                    handleExecute(
                                      action.id
                                    )
                                  }
                                >

                                  {
                                    action.action_type
                                    === "calendar"
                                      ? (
                                          isBusy
                                            ? "Creating..."
                                            : "Create Event"
                                        )
                                      : action.action_type
                                        === "webhook"
                                          ? (
                                              isBusy
                                                ? "Executing..."
                                                : "Execute Webhook"
                                            )
                                          : (
                                              isBusy
                                                ? "Sending..."
                                                : "Send Email"
                                            )
                                  }

                                </button>

                              </div>
                            )
                          }


                          {
                            action.status
                            === "pending"
                            && (

                              <div className="cf-action-card-actions">

                                <button
                                  type="button"

                                  className="secondary"

                                  disabled={
                                    isBusy
                                  }

                                  onClick={() =>
                                    startEdit(
                                      action
                                    )
                                  }
                                >
                                  Edit
                                </button>


                                <button
                                  type="button"

                                  className="danger"

                                  disabled={
                                    isBusy
                                  }

                                  onClick={() =>
                                    handleReject(
                                      action.id
                                    )
                                  }
                                >

                                  {
                                    isBusy
                                      ? "Working..."
                                      : "Reject"
                                  }

                                </button>


                                <button
                                  type="button"

                                  className="primary"

                                  disabled={
                                    isBusy
                                  }

                                  onClick={() =>
                                    handleApprove(
                                      action.id
                                    )
                                  }
                                >

                                  {
                                    isBusy
                                      ? "Working..."
                                      : "Approve"
                                  }

                                </button>

                              </div>

                            )
                          }

                        </article>

                      );

                    }
                  )
                }

              </div>

            )
          }

        </section>

      </main>


      {/* =================================================
          Edit Modal
      ================================================= */}

      {
        editingAction
        && (

          <div className="cf-action-modal-backdrop">

            <form
              className="cf-action-modal"

              onSubmit={
                saveEdit
              }
            >

              <div className="cf-action-modal-header">

                <div>

                  <span>
                    Review before approval
                  </span>

                  <h3>
                    Edit action
                  </h3>

                </div>


                <button
                  type="button"

                  className="cf-action-modal-close"

                  onClick={
                    closeEdit
                  }
                >
                  ×
                </button>

              </div>


              <label className="cf-action-field">

                <span>
                  Action title
                </span>

                <input
                  value={
                    editTitle
                  }

                  maxLength={
                    255
                  }

                  onChange={
                    event =>
                      setEditTitle(
                        event.target.value
                      )
                  }
                />

              </label>


              {
                editingAction.action_type
                === "email"
                && (
                  <>

                    <label className="cf-action-field">

                      <span>
                        Recipient
                      </span>

                      <input
                        type="email"

                        value={
                          editEmailTo
                        }

                        onChange={
                          event =>
                            setEditEmailTo(
                              event.target.value
                            )
                        }
                      />

                    </label>


                    <label className="cf-action-field">

                      <span>
                        Subject
                      </span>

                      <input
                        value={
                          editEmailSubject
                        }

                        onChange={
                          event =>
                            setEditEmailSubject(
                              event.target.value
                            )
                        }
                      />

                    </label>


                    <label className="cf-action-field">

                      <span>
                        Message
                      </span>

                      <textarea
                        rows={
                          9
                        }

                        value={
                          editEmailBody
                        }

                        onChange={
                          event =>
                            setEditEmailBody(
                              event.target.value
                            )
                        }
                      />

                    </label>

                  </>
                )
              }


              {
                editingAction.action_type
                === "calendar"
                && (
                  <>

                    <label className="cf-action-field">
                      <span>
                        Event title
                      </span>

                      <input
                        value={
                          editCalendarTitle
                        }

                        onChange={
                          event =>
                            setEditCalendarTitle(
                              event.target.value
                            )
                        }
                      />
                    </label>


                    <label className="cf-action-field">
                      <span>
                        Start time
                      </span>

                      <input
                        value={
                          editCalendarStart
                        }

                        placeholder="2026-09-24T15:00:00+05:30"

                        onChange={
                          event =>
                            setEditCalendarStart(
                              event.target.value
                            )
                        }
                      />
                    </label>


                    <label className="cf-action-field">
                      <span>
                        End time
                      </span>

                      <input
                        value={
                          editCalendarEnd
                        }

                        placeholder="2026-09-24T16:00:00+05:30"

                        onChange={
                          event =>
                            setEditCalendarEnd(
                              event.target.value
                            )
                        }
                      />
                    </label>


                    <label className="cf-action-field">
                      <span>
                        Timezone
                      </span>

                      <input
                        value={
                          editCalendarTimezone
                        }

                        placeholder="Asia/Colombo"

                        onChange={
                          event =>
                            setEditCalendarTimezone(
                              event.target.value
                            )
                        }
                      />
                    </label>


                    <label className="cf-action-field">
                      <span>
                        Description
                      </span>

                      <textarea
                        rows={
                          6
                        }

                        value={
                          editCalendarDescription
                        }

                        onChange={
                          event =>
                            setEditCalendarDescription(
                              event.target.value
                            )
                        }
                      />
                    </label>

                  </>
                )
              }


              {
                editingAction.action_type
                === "webhook"
                && (
                  <>

                    <label className="cf-action-field">
                      <span>
                        Webhook target
                      </span>

                      <input
                        value="demo_echo"
                        readOnly
                      />
                    </label>


                    <label className="cf-action-field">
                      <span>
                        JSON data
                      </span>

                      <textarea
                        rows={
                          10
                        }

                        value={
                          editWebhookDataJson
                        }

                        onChange={
                          event =>
                            setEditWebhookDataJson(
                              event.target.value
                            )
                        }
                      />
                    </label>

                  </>
                )
              }


              {
                editingAction.action_type
                !== "email"
                && editingAction.action_type
                !== "calendar"
                && editingAction.action_type
                !== "webhook"
                && (

                  <div className="cf-action-modal-info">

                    Editing payload fields
                    for this action type will
                    be added in a later phase.

                  </div>

                )
              }


              <div className="cf-action-modal-actions">

                <button
                  type="button"

                  className="secondary"

                  onClick={
                    closeEdit
                  }
                >
                  Cancel
                </button>


                <button
                  type="submit"

                  className="primary"

                  disabled={
                    busyActionId
                    === editingAction.id
                  }
                >

                  {
                    busyActionId
                    === editingAction.id

                      ? "Saving..."
                      : "Save changes"
                  }

                </button>

              </div>

            </form>

          </div>

        )
      }

    </div>

  );

}
