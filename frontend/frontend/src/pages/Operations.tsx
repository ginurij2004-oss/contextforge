import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  getAutomationAuditLogs,
  getOperationsHealth,
  getOperationsSummary,
  type AutomationAuditLogItem,
  type OperationsDailyPoint,
  type OperationsHealth,
  type OperationsSummary,
} from "../services/operations";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import "./Dashboard.css";
import "./Operations.css";


function formatDate(
  value: string | null | undefined
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


function eventLabel(
  value: string
) {
  return value
    .replaceAll(".", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, character =>
      character.toUpperCase()
    );
}


export default function Operations() {
  const navigate = useNavigate();

  const {
    theme,
    setTheme,
  } = useTheme();

  const {
    logout,
  } = useAuth();

  const [
    summary,
    setSummary,
  ] = useState<OperationsSummary | null>(null);

  const [
    health,
    setHealth,
  ] = useState<OperationsHealth | null>(null);

  const [
    logs,
    setLogs,
  ] = useState<AutomationAuditLogItem[]>([]);

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


  const loadData = async (
    silent = false
  ) => {
    try {
      if (silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const [
        summaryData,
        healthData,
        auditData,
      ] = await Promise.all([
        getOperationsSummary(),
        getOperationsHealth(),
        getAutomationAuditLogs(100),
      ]);

      setSummary(summaryData);
      setHealth(healthData);
      setLogs(auditData);
    } catch (error: any) {
      console.error(
        "LOAD OPERATIONS ERROR:",
        error
      );

      setError(
        error?.response?.data?.detail
        || "Failed to load operations data."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  useEffect(() => {
    loadData();
  }, []);


  const maxDailyRuns = useMemo(() => {
    if (!summary) {
      return 1;
    }

    return Math.max(
      1,
      ...summary.daily_runs.map((point: OperationsDailyPoint) =>
        point.completed
        + point.failed
        + point.other
      )
    );
  }, [summary]);


  const handleLogout = () => {
    logout();
    navigate("/login");
  };


  if (loading) {
    return (
      <div className="cf-page-loader">
        Loading Operations Center...
      </div>
    );
  }


  return (
    <div className="cf-dashboard cf-operations-page">

      {
        mobileSidebarOpen
        && (
          <button
            type="button"
            className="cf-mobile-overlay"
            onClick={() =>
              setMobileSidebarOpen(false)
            }
          />
        )
      }

      <aside
        className={
          mobileSidebarOpen
            ? "cf-sidebar cf-sidebar-open"
            : "cf-sidebar"
        }
      >
        <div className="cf-sidebar-brand">
          <div className="cf-sidebar-logo">C</div>
          <div className="cf-sidebar-brand-copy">
            <strong>ContextForge</strong>
            <span>Enterprise AI</span>
          </div>
          <button
            type="button"
            className="cf-sidebar-mobile-close"
            onClick={() =>
              setMobileSidebarOpen(false)
            }
          >
            ×
          </button>
        </div>

        <button
          type="button"
          className="cf-new-chat"
          onClick={() =>
            navigate("/dashboard")
          }
        >
          <span className="cf-new-chat-icon">✦</span>
          Back to workspace
        </button>

        <nav className="cf-sidebar-nav">
          <button type="button" onClick={() => navigate("/dashboard")}>
            <span className="cf-nav-icon">✦</span>
            AI Workspace
          </button>
          <button type="button" onClick={() => navigate("/documents")}>
            <span className="cf-nav-icon">◫</span>
            Documents
          </button>
          <button type="button" onClick={() => navigate("/analytics")}>
            <span className="cf-nav-icon">◩</span>
            Analytics
          </button>
          <button type="button" onClick={() => navigate("/actions")}>
            <span className="cf-nav-icon">⚡</span>
            Action Center
          </button>
          <button type="button" onClick={() => navigate("/automations")}>
            <span className="cf-nav-icon">⟳</span>
            Automations
          </button>
          <button type="button" className="active">
            <span className="cf-nav-icon">◎</span>
            Operations
          </button>
        </nav>

        <div className="cf-ops-sidebar-card">
          <span>Phase 8</span>
          <strong>Production operations</strong>
          <p>
            Monitor execution health, audit events and automation reliability.
          </p>
        </div>

        <div className="cf-sidebar-footer">
          <div className="cf-system-online">
            <span className="cf-online-dot" />
            ContextForge online
          </div>
          <button type="button" onClick={handleLogout}>
            <span className="cf-nav-icon">↗</span>
            Sign out
          </button>
        </div>
      </aside>


      <main className="cf-workspace cf-ops-workspace">
        <header className="cf-workspace-header cf-ops-header">
          <div className="cf-header-left">
            <button
              type="button"
              className="cf-mobile-menu"
              onClick={() =>
                setMobileSidebarOpen(true)
              }
            >
              ☰
            </button>

            <div>
              <span className="cf-ops-eyebrow">Production intelligence</span>
              <h1>Operations Center</h1>
              <p>
                Reliability, audit history and execution health for ContextForge automations.
              </p>
            </div>
          </div>

          <div className="cf-ops-header-tools">
            <button
              type="button"
              className="cf-ops-theme"
              onClick={() =>
                setTheme(
                  theme === "dark"
                    ? "light"
                    : "dark"
                )
              }
            >
              {theme === "dark" ? "☀" : "☾"}
            </button>

            <button
              type="button"
              className="cf-ops-refresh"
              disabled={refreshing}
              onClick={() => loadData(true)}
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </header>


        <section className="cf-ops-content">
          {
            error
            && (
              <div className="cf-ops-alert error">
                {error}
              </div>
            )
          }

          <div className="cf-ops-health-row">
            <div className="cf-ops-health-copy">
              <span>System health</span>
              <strong>
                {health?.status === "healthy" ? "All core services ready" : "Attention required"}
              </strong>
              <p>
                Checked {formatDate(health?.checked_at)}
              </p>
            </div>

            <div className="cf-ops-health-pills">
              <span className={health?.database === "healthy" ? "ok" : "bad"}>
                Database · {health?.database || "unknown"}
              </span>
              <span className={health?.scheduler === "running" ? "ok" : "bad"}>
                Scheduler · {health?.scheduler || "unknown"}
              </span>
              <span className={health?.n8n_configured ? "ok" : "warn"}>
                n8n · {health?.n8n_configured ? "configured" : "not configured"}
              </span>
            </div>
          </div>


          <div className="cf-ops-stats">
            <article>
              <span>Enabled automations</span>
              <strong>{summary?.automations_enabled ?? 0}</strong>
              <small>{summary?.automations_total ?? 0} total</small>
            </article>
            <article>
              <span>Success rate</span>
              <strong>{summary?.success_rate ?? 0}%</strong>
              <small>Completed vs failed runs</small>
            </article>
            <article>
              <span>Pending approvals</span>
              <strong>{summary?.pending_actions ?? 0}</strong>
              <small>Waiting in Action Center</small>
            </article>
            <article>
              <span>Upcoming</span>
              <strong>{summary?.upcoming_runs ?? 0}</strong>
              <small>Scheduled future triggers</small>
            </article>
            <article>
              <span>Completed runs</span>
              <strong>{summary?.runs_completed ?? 0}</strong>
              <small>{summary?.runs_total ?? 0} total runs</small>
            </article>
            <article className="danger">
              <span>Failed runs</span>
              <strong>{summary?.runs_failed ?? 0}</strong>
              <small>{summary?.failed_actions ?? 0} failed actions</small>
            </article>
          </div>


          <div className="cf-ops-grid">
            <section className="cf-ops-panel">
              <div className="cf-ops-panel-heading">
                <div>
                  <span>7-day execution trend</span>
                  <h2>Automation activity</h2>
                </div>
              </div>

              <div className="cf-ops-bars">
                {
                  summary?.daily_runs.map((point: OperationsDailyPoint) => {
                    const total = (
                      point.completed
                      + point.failed
                      + point.other
                    );
                    const height = Math.max(
                      total === 0 ? 5 : 16,
                      (total / maxDailyRuns) * 100
                    );

                    return (
                      <div className="cf-ops-bar-column" key={point.date}>
                        <div className="cf-ops-bar-track">
                          <div
                            className="cf-ops-bar-fill"
                            style={{ height: `${height}%` }}
                            title={`${total} run(s)`}
                          />
                        </div>
                        <strong>{total}</strong>
                        <span>
                          {new Date(`${point.date}T00:00:00`).toLocaleDateString(undefined, {
                            weekday: "short",
                          })}
                        </span>
                      </div>
                    );
                  })
                }
              </div>

              <div className="cf-ops-legend">
                <span>Completed: {summary?.runs_completed ?? 0}</span>
                <span>Failed: {summary?.runs_failed ?? 0}</span>
                <span>In progress: {summary?.runs_pending ?? 0}</span>
              </div>
            </section>


            <section className="cf-ops-panel">
              <div className="cf-ops-panel-heading">
                <div>
                  <span>Quick navigation</span>
                  <h2>Operations shortcuts</h2>
                </div>
              </div>

              <div className="cf-ops-shortcuts">
                <button type="button" onClick={() => navigate("/actions")}>
                  <span>⚡</span>
                  <div>
                    <strong>Action Center</strong>
                    <small>Review, approve and retry failed actions</small>
                  </div>
                </button>
                <button type="button" onClick={() => navigate("/automations")}>
                  <span>⟳</span>
                  <div>
                    <strong>Automation Builder</strong>
                    <small>Schedules, auto execution and run history</small>
                  </div>
                </button>
              </div>
            </section>
          </div>


          <section className="cf-ops-panel cf-ops-audit-panel">
            <div className="cf-ops-panel-heading">
              <div>
                <span>Application event history</span>
                <h2>Recent audit events</h2>
              </div>
              <small>{logs.length} loaded</small>
            </div>

            {
              logs.length === 0
              ? (
                <div className="cf-ops-empty">
                  No Phase 8 audit events yet. Create, run, approve or execute an automation to populate this timeline.
                </div>
              )
              : (
                <div className="cf-ops-audit-list">
                  {
                    logs.map((log: AutomationAuditLogItem) => (
                      <article key={log.id}>
                        <div className={`cf-ops-audit-dot ${log.status}`} />
                        <div className="cf-ops-audit-copy">
                          <div>
                            <strong>{eventLabel(log.event_type)}</strong>
                            <span className={`cf-ops-audit-status ${log.status}`}>
                              {log.status}
                            </span>
                          </div>
                          <p>{log.message}</p>
                          <small>
                            {formatDate(log.created_at)}
                            {log.automation_id ? ` · Automation #${log.automation_id}` : ""}
                            {log.action_request_id ? ` · Action #${log.action_request_id}` : ""}
                          </small>
                        </div>
                      </article>
                    ))
                  }
                </div>
              )
            }
          </section>
        </section>
      </main>
    </div>
  );
}
