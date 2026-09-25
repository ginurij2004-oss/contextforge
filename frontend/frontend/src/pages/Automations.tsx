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
  createAutomation,
  deleteAutomation,
  getAutomationRuns,
  getAutomations,
  getUpcomingAutomations,
  runAutomation,
  updateAutomation,
  type AutomationActionType,
  type AutomationItem,
  type AutomationRunItem,
  type AutomationTriggerType,
} from "../services/automations";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import "./Dashboard.css";
import "./Automations.css";


type ViewMode =
  | "automations"
  | "upcoming"
  | "history";


const ACTION_TYPES:
  AutomationActionType[] = [
    "email",
    "calendar",
    "webhook",
  ];


const TRIGGER_TYPES:
  AutomationTriggerType[] = [
    "manual",
    "once",
    "daily",
    "weekdays",
    "weekly",
    "interval",
  ];


const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];


type Meridiem = "AM" | "PM";


type ParsedTime = {
  time12: string;
  time24: string;
  meridiem: Meridiem;
};


function parseFlexibleTime(
  value: string,
  selectedMeridiem: Meridiem
): ParsedTime {
  let raw = value
    .trim()
    .toUpperCase();

  if (!raw) {
    throw new Error(
      "Enter a time, for example 1:45 PM or 13:45."
    );
  }

  let meridiem = selectedMeridiem;

  const suffixMatch = raw.match(/\s*(AM|PM)$/);

  if (suffixMatch) {
    meridiem = suffixMatch[1] as Meridiem;
    raw = raw
      .replace(/\s*(AM|PM)$/, "")
      .trim();
  }

  // Friendly input support:
  // 1:45, 1.45, 145, 01:45, 13:45, 1345, 9
  raw = raw.replace(/\./g, ":");

  let hour: number;
  let minute: number;

  if (raw.includes(":")) {
    const parts = raw.split(":");

    if (
      parts.length !== 2
      || !/^\d{1,2}$/.test(parts[0])
      || !/^\d{1,2}$/.test(parts[1])
    ) {
      throw new Error(
        "Enter a valid time such as 1:45, 13:45 or 1345."
      );
    }

    hour = Number(parts[0]);
    minute = Number(parts[1]);
  } else {
    if (!/^\d{1,4}$/.test(raw)) {
      throw new Error(
        "Enter a valid time such as 1:45, 13:45 or 1345."
      );
    }

    if (raw.length <= 2) {
      hour = Number(raw);
      minute = 0;
    } else if (raw.length === 3) {
      hour = Number(raw.slice(0, 1));
      minute = Number(raw.slice(1));
    } else {
      hour = Number(raw.slice(0, 2));
      minute = Number(raw.slice(2));
    }
  }

  if (
    Number.isNaN(hour)
    || Number.isNaN(minute)
    || hour < 0
    || hour > 23
    || minute < 0
    || minute > 59
  ) {
    throw new Error(
      "Enter a valid time. Hours must be 1–12 with AM/PM, or 00–23 in 24-hour format; minutes must be 00–59."
    );
  }

  let hour24: number;

  // 00:xx and 13:xx–23:xx are unambiguously 24-hour input.
  // Example: 13.45 automatically becomes 1:45 PM even if AM was selected.
  if (hour === 0 || hour > 12) {
    hour24 = hour;
    meridiem = hour24 >= 12 ? "PM" : "AM";
  } else {
    hour24 = hour % 12;

    if (meridiem === "PM") {
      hour24 += 12;
    }
  }

  const hour12 = hour24 % 12 || 12;

  return {
    time12: `${hour12}:${String(minute).padStart(2, "0")}`,
    time24: `${String(hour24).padStart(2, "0")}:${String(minute).padStart(2, "0")}`,
    meridiem,
  };
}


function twelveHourTo24Hour(
  value: string,
  meridiem: Meridiem
) {
  return parseFlexibleTime(
    value,
    meridiem
  ).time24;
}


function twentyFourHourTo12Hour(
  value: string
): { time: string; meridiem: Meridiem } {
  try {
    const parsed = parseFlexibleTime(
      value,
      "AM"
    );

    return {
      time: parsed.time12,
      meridiem: parsed.meridiem,
    };
  } catch {
    return {
      time: "9:00",
      meridiem: "AM",
    };
  }
}


function formatTwelveHourTime(
  value: string,
  meridiem: Meridiem
) {
  try {
    const parsed = parseFlexibleTime(
      value,
      meridiem
    );

    return `${parsed.time12} ${parsed.meridiem}`;
  } catch {
    return `${value || "—"} ${meridiem}`;
  }
}


function formatDate(
  value: string | null
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString();
}


function actionIcon(
  actionType: AutomationActionType
) {
  switch (actionType) {
    case "email":
      return "✉";
    case "calendar":
      return "▦";
    case "webhook":
      return "↗";
    default:
      return "⚡";
  }
}


function actionLabel(
  actionType: AutomationActionType
) {
  switch (actionType) {
    case "email":
      return "Email";
    case "calendar":
      return "Calendar";
    case "webhook":
      return "Webhook";
    default:
      return actionType;
  }
}


function triggerLabel(
  triggerType: AutomationTriggerType,
  schedule?: Record<string, unknown> | null
) {
  if (triggerType === "manual") {
    return "Manual";
  }

  if (triggerType === "once") {
    return "One time";
  }

  if (triggerType === "daily") {
    return `Daily ${String(schedule?.time || "")}`.trim();
  }

  if (triggerType === "weekdays") {
    return `Weekdays ${String(schedule?.time || "")}`.trim();
  }

  if (triggerType === "weekly") {
    const day = String(
      schedule?.weekday || "weekly"
    );

    return `${day.charAt(0).toUpperCase()}${day.slice(1)} ${String(schedule?.time || "")}`.trim();
  }

  if (triggerType === "interval") {
    return `Every ${String(schedule?.hours || "—")}h`;
  }

  return triggerType;
}


function runStatusLabel(
  value: string
) {
  return value
    .replace(/_/g, " ")
    .replace(
      /\b\w/g,
      character =>
        character.toUpperCase()
    );
}


function localInputToColomboIso(
  value: string
) {
  const trimmed = value.trim();

  if (!trimmed) {
    return "";
  }

  const withSeconds =
    trimmed.length === 16
      ? `${trimmed}:00`
      : trimmed;

  return `${withSeconds}+05:30`;
}


function isoToLocalInput(
  value: unknown
) {
  if (
    typeof value !== "string"
    || !value
  ) {
    return "";
  }

  return value.slice(0, 16);
}


function configText(
  automation: AutomationItem
) {
  if (automation.action_type === "email") {
    return String(
      automation.config.to
      || "Recipient not set"
    );
  }

  if (automation.action_type === "calendar") {
    return String(
      automation.config.title
      || "Calendar event"
    );
  }

  return String(
    automation.config.target
    || "Webhook target"
  );
}


function nextRunText(
  automation: AutomationItem
) {
  if (automation.trigger_type === "manual") {
    return "Manual only";
  }

  if (!automation.next_run_at) {
    return automation.trigger_type === "once"
      ? "Schedule completed"
      : "No upcoming run";
  }

  return formatDate(
    automation.next_run_at
  );
}


export default function Automations() {
  const navigate = useNavigate();

  const {
    theme,
    setTheme,
  } = useTheme();

  const {
    logout,
  } = useAuth();

  const [
    automations,
    setAutomations,
  ] = useState<AutomationItem[]>([]);

  const [
    upcoming,
    setUpcoming,
  ] = useState<AutomationItem[]>([]);

  const [
    runs,
    setRuns,
  ] = useState<AutomationRunItem[]>([]);

  const [
    viewMode,
    setViewMode,
  ] = useState<ViewMode>(
    "automations"
  );

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyAutomationId, setBusyAutomationId] = useState<number | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingAutomation, setEditingAutomation] = useState<AutomationItem | null>(null);
  const [editorStep, setEditorStep] = useState(1);

  const [actionType, setActionType] = useState<AutomationActionType>("email");
  const [triggerType, setTriggerType] = useState<AutomationTriggerType>("manual");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isEnabled, setIsEnabled] = useState(true);
  const [requiresApproval, setRequiresApproval] = useState(true);

  const [scheduleTimezone] = useState("Asia/Colombo");
  const [onceDate, setOnceDate] = useState("");
  const [onceTime, setOnceTime] = useState("9:00");
  const [onceMeridiem, setOnceMeridiem] = useState<Meridiem>("AM");
  const [scheduleTime, setScheduleTime] = useState("09:00");
  const [weeklyDay, setWeeklyDay] = useState("monday");
  const [intervalHours, setIntervalHours] = useState("6");
  const [intervalStart, setIntervalStart] = useState("");

  const [emailTo, setEmailTo] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");

  const [calendarTitle, setCalendarTitle] = useState("");
  const [calendarStart, setCalendarStart] = useState("");
  const [calendarEnd, setCalendarEnd] = useState("");
  const [calendarDescription, setCalendarDescription] = useState("");
  const [calendarTimezone] = useState("Asia/Colombo");

  const [webhookDataJson, setWebhookDataJson] = useState(`{
  "message": "Hello from ContextForge"
}`);


  useEffect(() => {
    loadData();
  }, []);


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
        automationData,
        runData,
        upcomingData,
      ] = await Promise.all([
        getAutomations(),
        getAutomationRuns(75),
        getUpcomingAutomations(25),
      ]);

      setAutomations(automationData);
      setRuns(runData);
      setUpcoming(upcomingData);

    } catch (error: any) {
      console.error(
        "LOAD AUTOMATIONS ERROR:",
        error
      );

      setError(
        error?.response?.data?.detail
        || "Failed to load automations."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  const stats = useMemo(
    () => {
      const enabled = automations.filter(
        item => item.is_enabled
      ).length;

      const scheduled = automations.filter(
        item => item.trigger_type !== "manual"
      ).length;

      const waiting = runs.filter(
        run => run.status === "pending_approval"
      ).length;

      return {
        total: automations.length,
        enabled,
        scheduled,
        waiting,
      };
    },
    [automations, runs]
  );


  const resetEditor = () => {
    setEditingAutomation(null);
    setEditorStep(1);

    setActionType("email");
    setTriggerType("manual");
    setName("");
    setDescription("");
    setIsEnabled(true);
    setRequiresApproval(true);

    setOnceDate("");
    setOnceTime("9:00");
    setOnceMeridiem("AM");
    setScheduleTime("09:00");
    setWeeklyDay("monday");
    setIntervalHours("6");
    setIntervalStart("");

    setEmailTo("");
    setEmailSubject("");
    setEmailBody("");

    setCalendarTitle("");
    setCalendarStart("");
    setCalendarEnd("");
    setCalendarDescription("");

    setWebhookDataJson(`{
  "message": "Hello from ContextForge"
}`);
  };


  const openCreate = (
    type: AutomationActionType
  ) => {
    resetEditor();
    setError("");
    setActionType(type);
    setEditorOpen(true);
  };


  const openEdit = (
    automation: AutomationItem
  ) => {
    resetEditor();
    setError("");

    setEditingAutomation(automation);
    setActionType(automation.action_type);
    setTriggerType(automation.trigger_type);
    setName(automation.name);
    setDescription(automation.description || "");
    setIsEnabled(automation.is_enabled);
    setRequiresApproval(automation.requires_approval);

    const schedule = automation.schedule || {};

    if (automation.trigger_type === "once") {
      const localRunAt = isoToLocalInput(
        schedule.run_at
      );

      setOnceDate(
        localRunAt.slice(0, 10)
      );

      const savedTime = twentyFourHourTo12Hour(
        localRunAt.slice(11, 16) || "09:00"
      );

      setOnceTime(savedTime.time);
      setOnceMeridiem(savedTime.meridiem);
    }

    if (
      automation.trigger_type === "daily"
      || automation.trigger_type === "weekdays"
      || automation.trigger_type === "weekly"
    ) {
      setScheduleTime(
        String(
          schedule.time || "09:00"
        )
      );
    }

    if (automation.trigger_type === "weekly") {
      setWeeklyDay(
        String(
          schedule.weekday || "monday"
        )
      );
    }

    if (automation.trigger_type === "interval") {
      setIntervalHours(
        String(
          schedule.hours || "6"
        )
      );

      setIntervalStart(
        isoToLocalInput(
          schedule.start_at
        )
      );
    }

    if (automation.action_type === "email") {
      setEmailTo(String(automation.config.to || ""));
      setEmailSubject(String(automation.config.subject || ""));
      setEmailBody(String(automation.config.body || ""));
    }

    if (automation.action_type === "calendar") {
      setCalendarTitle(String(automation.config.title || ""));
      setCalendarStart(isoToLocalInput(automation.config.start_time));
      setCalendarEnd(isoToLocalInput(automation.config.end_time));
      setCalendarDescription(String(automation.config.description || ""));
    }

    if (automation.action_type === "webhook") {
      try {
        setWebhookDataJson(
          JSON.stringify(
            automation.config.data || {},
            null,
            2
          )
        );
      } catch {
        setWebhookDataJson("{}");
      }
    }

    setEditorOpen(true);
  };


  const closeEditor = () => {
    setEditorOpen(false);
    resetEditor();
  };


  const buildSchedule = (): Record<string, unknown> | null => {
    if (triggerType === "manual") {
      return null;
    }

    if (triggerType === "once") {
      if (!onceDate || !onceTime) {
        throw new Error(
          "Choose the one-time run date and time."
        );
      }

      const normalizedTime = twelveHourTo24Hour(
        onceTime,
        onceMeridiem
      );

      const runAt = localInputToColomboIso(
        `${onceDate}T${normalizedTime}`
      );

      return {
        run_at: runAt,
      };
    }

    if (
      triggerType === "daily"
      || triggerType === "weekdays"
    ) {
      if (!scheduleTime.trim()) {
        throw new Error(
          "Choose a schedule time."
        );
      }

      return {
        time: scheduleTime.trim(),
        timezone: scheduleTimezone,
      };
    }

    if (triggerType === "weekly") {
      return {
        weekday: weeklyDay,
        time: scheduleTime.trim(),
        timezone: scheduleTimezone,
      };
    }

    const hours = Number(
      intervalHours
    );

    const startAt = localInputToColomboIso(
      intervalStart
    );

    if (
      !Number.isInteger(hours)
      || hours < 1
      || hours > 720
    ) {
      throw new Error(
        "Interval must be between 1 and 720 hours."
      );
    }

    if (!startAt) {
      throw new Error(
        "Choose the interval start date and time."
      );
    }

    return {
      hours,
      start_at: startAt,
    };
  };


  const buildConfig = () => {
    if (actionType === "email") {
      const to = emailTo.trim();
      const subject = emailSubject.trim();
      const body = emailBody.trim();

      if (!to || !subject || !body) {
        throw new Error(
          "Recipient, subject and message are required."
        );
      }

      return {
        to,
        subject,
        body,
      };
    }

    if (actionType === "calendar") {
      const title = calendarTitle.trim();
      const startTime = localInputToColomboIso(calendarStart);
      const endTime = localInputToColomboIso(calendarEnd);

      if (!title || !startTime || !endTime) {
        throw new Error(
          "Calendar title, start and end are required."
        );
      }

      return {
        title,
        start_time: startTime,
        end_time: endTime,
        description: calendarDescription.trim(),
        timezone: calendarTimezone,
      };
    }

    let data: Record<string, unknown>;

    try {
      const parsed = JSON.parse(
        webhookDataJson
      );

      if (
        !parsed
        || Array.isArray(parsed)
        || typeof parsed !== "object"
      ) {
        throw new Error();
      }

      data = parsed as Record<string, unknown>;
    } catch {
      throw new Error(
        "Webhook data must be a valid JSON object."
      );
    }

    return {
      target: "demo_echo",
      data,
    };
  };


  const validateStep = (
    targetStep: number
  ) => {
    setError("");

    try {
      if (
        editorStep === 1
        && !name.trim()
      ) {
        throw new Error(
          "Automation name is required."
        );
      }

      if (editorStep === 3) {
        buildSchedule();
      }

      if (editorStep === 4) {
        buildConfig();
      }

      setEditorStep(targetStep);
    } catch (error: any) {
      setError(
        error?.message
        || "Check the automation configuration."
      );
    }
  };


  const handleSave = async (
    event: FormEvent
  ) => {
    event.preventDefault();

    try {
      setError("");
      setNotice("");

      const cleanName = name.trim();

      if (!cleanName) {
        throw new Error(
          "Automation name is required."
        );
      }

      const schedule = buildSchedule();
      const config = buildConfig();

      if (editingAutomation) {
        setBusyAutomationId(
          editingAutomation.id
        );

        const updated = await updateAutomation(
          editingAutomation.id,
          {
            name: cleanName,
            description: description.trim() || null,
            trigger_type: triggerType,
            schedule,
            config,
            is_enabled: isEnabled,
            requires_approval: requiresApproval,
          }
        );

        setAutomations(previous =>
          previous.map(item =>
            item.id === updated.id
              ? updated
              : item
          )
        );

        setNotice(
          "Automation updated successfully."
        );
      } else {
        const created = await createAutomation({
          name: cleanName,
          description: description.trim() || null,
          trigger_type: triggerType,
          schedule,
          action_type: actionType,
          config,
          is_enabled: isEnabled,
          requires_approval: requiresApproval,
        });

        setAutomations(previous => [
          created,
          ...previous,
        ]);

        setNotice(
          triggerType === "manual"
            ? "Automation created successfully."
            : "Scheduled automation created successfully."
        );
      }

      closeEditor();
      await loadData(true);

    } catch (error: any) {
      console.error(
        "SAVE AUTOMATION ERROR:",
        error
      );

      setError(
        error?.response?.data?.detail
        || error?.message
        || "Failed to save automation."
      );
    } finally {
      setBusyAutomationId(null);
    }
  };


  const handleToggle = async (
    automation: AutomationItem
  ) => {
    try {
      setBusyAutomationId(
        automation.id
      );
      setError("");
      setNotice("");

      const updated = await updateAutomation(
        automation.id,
        {
          is_enabled: !automation.is_enabled,
        }
      );

      setAutomations(previous =>
        previous.map(item =>
          item.id === updated.id
            ? updated
            : item
        )
      );

      await loadData(true);
    } catch (error: any) {
      setError(
        error?.response?.data?.detail
        || "Failed to update automation."
      );
    } finally {
      setBusyAutomationId(null);
    }
  };


  const handleDelete = async (
    automation: AutomationItem
  ) => {
    const confirmed = window.confirm(
      `Delete "${automation.name}"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setBusyAutomationId(
        automation.id
      );
      setError("");
      setNotice("");

      await deleteAutomation(
        automation.id
      );

      setAutomations(previous =>
        previous.filter(item =>
          item.id !== automation.id
        )
      );

      setRuns(previous =>
        previous.filter(run =>
          run.automation_id !== automation.id
        )
      );

      setUpcoming(previous =>
        previous.filter(item =>
          item.id !== automation.id
        )
      );

      setNotice(
        "Automation deleted."
      );
    } catch (error: any) {
      setError(
        error?.response?.data?.detail
        || "Failed to delete automation."
      );
    } finally {
      setBusyAutomationId(null);
    }
  };


  const handleRun = async (
    automation: AutomationItem
  ) => {
    try {
      setBusyAutomationId(
        automation.id
      );
      setError("");
      setNotice("");

      const run = await runAutomation(
        automation.id
      );

      setRuns(previous => [
        run,
        ...previous,
      ]);

      setNotice(
        automation.requires_approval
          ? "Pending action created. Review it in Action Center before execution."
          : run.status === "completed"
            ? "Automation executed automatically and completed successfully."
            : run.status === "failed"
              ? "Automation auto-executed but failed. Check Run History."
              : `Automation started automatically. Status: ${runStatusLabel(run.status)}.`
      );
    } catch (error: any) {
      setError(
        error?.response?.data?.detail
        || "Failed to run automation."
      );
    } finally {
      setBusyAutomationId(null);
    }
  };


  const handleLogout = () => {
    logout();
    navigate("/login");
  };


  if (loading) {
    return (
      <div className="cf-dashboard-loading">
        <div className="cf-dashboard-loading-logo">
          C
        </div>
        <span>
          Loading Automation Builder...
        </span>
      </div>
    );
  }


  return (
    <div className="cf-dashboard cf-automations-page">

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
          <div className="cf-sidebar-logo">
            C
          </div>
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
          <button type="button" className="active">
            <span className="cf-nav-icon">⟳</span>
            Automations
          </button>
          <button type="button" onClick={() => navigate("/operations")}>
            <span className="cf-nav-icon">◎</span>
            Operations
          </button>
        </nav>

        <div className="cf-auto-sidebar-card">
          <span>Phase 7 scheduler</span>
          <strong>Approval or auto execution</strong>
          <p>
            Each automation can require Action Center approval or auto-execute through n8n when its trigger fires.
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


      <main className="cf-workspace cf-auto-workspace">
        <header className="cf-workspace-header cf-auto-header">
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
              <span className="cf-header-eyebrow">
                Phase 7
              </span>
              <h1>Automation Builder</h1>
              <p>
                Manual, one-time and recurring workflows with configurable approval or auto execution.
              </p>
            </div>
          </div>

          <div className="cf-auto-header-tools">
            <button
              type="button"
              className="cf-auto-secondary"
              onClick={() => loadData(true)}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
            <button
              type="button"
              className="cf-auto-theme"
              onClick={() =>
                setTheme(
                  theme === "dark"
                    ? "light"
                    : "dark"
                )
              }
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "☀" : "☾"}
            </button>
            <button
              type="button"
              className="cf-auto-primary"
              onClick={() => openCreate("email")}
            >
              + Create automation
            </button>
          </div>
        </header>


        <div className="cf-auto-content">
          {
            error
            && (
              <div className="cf-auto-alert error">
                {error}
              </div>
            )
          }

          {
            notice
            && (
              <div className="cf-auto-alert success">
                <span>{notice}</span>
                {
                  notice.includes("Pending action")
                  && (
                    <button
                      type="button"
                      onClick={() => navigate("/actions")}
                    >
                      Open Action Center
                    </button>
                  )
                }
              </div>
            )
          }


          <section className="cf-auto-stats">
            <article>
              <span>Total</span>
              <strong>{stats.total}</strong>
              <small>Saved automations</small>
            </article>
            <article>
              <span>Enabled</span>
              <strong>{stats.enabled}</strong>
              <small>Active templates</small>
            </article>
            <article>
              <span>Scheduled</span>
              <strong>{stats.scheduled}</strong>
              <small>Recurring or one-time</small>
            </article>
            <article>
              <span>Waiting</span>
              <strong>{stats.waiting}</strong>
              <small>Pending approval</small>
            </article>
          </section>


          <section className="cf-auto-templates">
            <div className="cf-auto-section-heading">
              <div>
                <span>Quick start</span>
                <h2>Automation templates</h2>
              </div>
              <p>
                Choose the action first, then select a manual or scheduled trigger.
              </p>
            </div>

            <div className="cf-auto-template-grid">
              <button type="button" onClick={() => openCreate("email")}>
                <b>✉</b>
                <strong>Send Email</strong>
                <span>Gmail through the existing n8n execution workflow.</span>
              </button>
              <button type="button" onClick={() => openCreate("calendar")}>
                <b>▦</b>
                <strong>Create Event</strong>
                <span>Google Calendar with approval-required or auto-execute mode.</span>
              </button>
              <button type="button" onClick={() => openCreate("webhook")}>
                <b>↗</b>
                <strong>Send Webhook</strong>
                <span>Allowlisted webhook execution through n8n.</span>
              </button>
            </div>
          </section>


          <div className="cf-auto-tabs">
            <button
              type="button"
              className={viewMode === "automations" ? "active" : ""}
              onClick={() => setViewMode("automations")}
            >
              My Automations
            </button>
            <button
              type="button"
              className={viewMode === "upcoming" ? "active" : ""}
              onClick={() => setViewMode("upcoming")}
            >
              Upcoming Runs
            </button>
            <button
              type="button"
              className={viewMode === "history" ? "active" : ""}
              onClick={() => setViewMode("history")}
            >
              Run History
            </button>
          </div>


          {
            viewMode === "automations"
            && (
              <section className="cf-auto-list">
                {
                  automations.length === 0
                  ? (
                    <div className="cf-auto-empty">
                      <div>⟳</div>
                      <h3>No saved automations yet</h3>
                      <p>Create a manual or scheduled workflow.</p>
                    </div>
                  )
                  : automations.map(automation => {
                    const busy = busyAutomationId === automation.id;

                    return (
                      <article className="cf-auto-card" key={automation.id}>
                        <div className="cf-auto-card-icon">
                          {actionIcon(automation.action_type)}
                        </div>

                        <div className="cf-auto-card-main">
                          <div className="cf-auto-card-title-row">
                            <div>
                              <div className="cf-auto-card-badges">
                                <span>{actionLabel(automation.action_type)}</span>
                                <span>{triggerLabel(automation.trigger_type, automation.schedule)}</span>
                                <span className={automation.requires_approval ? "approval" : "auto-execute"}>
                                  {automation.requires_approval ? "Approval required" : "Auto execute"}
                                </span>
                                <span className={automation.is_enabled ? "enabled" : "disabled"}>
                                  {automation.is_enabled ? "Enabled" : "Disabled"}
                                </span>
                              </div>
                              <h3>{automation.name}</h3>
                            </div>
                            <small>
                              Updated {formatDate(automation.updated_at)}
                            </small>
                          </div>

                          <p className="cf-auto-description">
                            {automation.description || "No description"}
                          </p>

                          <div className="cf-auto-config-preview-grid">
                            <div className="cf-auto-config-preview">
                              <span>Configuration</span>
                              <strong>{configText(automation)}</strong>
                            </div>
                            <div className="cf-auto-config-preview schedule">
                              <span>Next run</span>
                              <strong>{nextRunText(automation)}</strong>
                            </div>
                          </div>

                          <div className="cf-auto-card-actions">
                            <button
                              type="button"
                              className="primary"
                              disabled={busy || !automation.is_enabled}
                              onClick={() => handleRun(automation)}
                            >
                              {busy ? "Working..." : "Run now"}
                            </button>
                            <button type="button" disabled={busy} onClick={() => openEdit(automation)}>
                              Edit
                            </button>
                            <button type="button" disabled={busy} onClick={() => handleToggle(automation)}>
                              {automation.is_enabled ? "Disable" : "Enable"}
                            </button>
                            <button type="button" className="danger" disabled={busy} onClick={() => handleDelete(automation)}>
                              Delete
                            </button>
                          </div>
                        </div>
                      </article>
                    );
                  })
                }
              </section>
            )
          }


          {
            viewMode === "upcoming"
            && (
              <section className="cf-auto-list">
                {
                  upcoming.length === 0
                  ? (
                    <div className="cf-auto-empty">
                      <div>◷</div>
                      <h3>No upcoming scheduled runs</h3>
                      <p>Create or enable a scheduled automation to see its next trigger.</p>
                    </div>
                  )
                  : upcoming.map(automation => (
                    <article className="cf-auto-upcoming-card" key={automation.id}>
                      <div className="cf-auto-card-icon">
                        {actionIcon(automation.action_type)}
                      </div>
                      <div>
                        <div className="cf-auto-card-badges">
                          <span>{triggerLabel(automation.trigger_type, automation.schedule)}</span>
                          <span className="enabled">Scheduled</span>
                        </div>
                        <h3>{automation.name}</h3>
                        <p>{actionLabel(automation.action_type)} · {configText(automation)}</p>
                      </div>
                      <div className="cf-auto-upcoming-time">
                        <span>Next trigger</span>
                        <strong>{formatDate(automation.next_run_at)}</strong>
                        <small>
                          {automation.requires_approval
                            ? "Creates a pending Action Center item."
                            : "Auto-executes through n8n at trigger time."}
                        </small>
                      </div>
                    </article>
                  ))
                }
              </section>
            )
          }


          {
            viewMode === "history"
            && (
              <section className="cf-auto-history">
                {
                  runs.length === 0
                  ? (
                    <div className="cf-auto-empty">
                      <div>◴</div>
                      <h3>No automation runs yet</h3>
                      <p>Manual and scheduled triggers will appear here.</p>
                    </div>
                  )
                  : (
                    <div className="cf-auto-history-table">
                      <div className="cf-auto-history-head cf-phase7-history-head">
                        <span>Automation</span>
                        <span>Source</span>
                        <span>Status</span>
                        <span>Created</span>
                        <span>Action</span>
                      </div>

                      {runs.map(run => (
                        <div className="cf-auto-history-row cf-phase7-history-row" key={run.id}>
                          <div>
                            <strong>{run.automation_name}</strong>
                            <small>{actionLabel(run.action_type)}</small>
                          </div>
                          <div>
                            <span className={`cf-auto-source ${run.trigger_source}`}>
                              {run.trigger_source === "schedule" ? "Scheduled" : "Manual"}
                            </span>
                            {
                              run.scheduled_for
                              && <small>{formatDate(run.scheduled_for)}</small>
                            }
                          </div>
                          <div>
                            <span className={`cf-auto-run-status ${run.status}`}>
                              {runStatusLabel(run.status)}
                            </span>
                            {run.error_message && <small className="error">{run.error_message}</small>}
                          </div>
                          <div>
                            <span>{formatDate(run.created_at)}</span>
                            {run.completed_at && <small>Completed {formatDate(run.completed_at)}</small>}
                          </div>
                          <div>
                            {
                              run.action_request_id
                              ? (
                                <button type="button" onClick={() => navigate("/actions")}>
                                  Action #{run.action_request_id}
                                </button>
                              )
                              : <span>—</span>
                            }
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                }
              </section>
            )
          }
        </div>
      </main>


      {
        editorOpen
        && (
          <div className="cf-auto-modal-backdrop" role="presentation">
            <div className="cf-auto-modal" role="dialog" aria-modal="true">
              <div className="cf-auto-modal-header">
                <div>
                  <span>{editingAutomation ? "Edit automation" : "Create automation"}</span>
                  <h2>{editingAutomation ? editingAutomation.name : "Automation Builder"}</h2>
                </div>
                <button type="button" onClick={closeEditor}>×</button>
              </div>

              <div className="cf-auto-wizard-progress cf-phase7-progress">
                {[
                  "Details",
                  "Action",
                  "Schedule",
                  "Configure",
                  "Review",
                ].map((label, index) => {
                  const step = index + 1;
                  return (
                    <div key={label} className={step <= editorStep ? "active" : ""}>
                      <b>{step}</b>
                      <span>{label}</span>
                    </div>
                  );
                })}
              </div>

              {error && <div className="cf-auto-modal-error">{error}</div>}

              <form onSubmit={handleSave}>
                <div className="cf-auto-modal-body">

                  {
                    editorStep === 1
                    && (
                      <div className="cf-auto-form-grid">
                        <label className="full">
                          <span>Automation name</span>
                          <input value={name} onChange={event => setName(event.target.value)} placeholder="Daily client follow-up" />
                        </label>
                        <label className="full">
                          <span>Description</span>
                          <textarea value={description} onChange={event => setDescription(event.target.value)} rows={4} placeholder="What this automation is for" />
                        </label>
                        <label className="cf-auto-toggle-row full">
                          <div>
                            <strong>Enabled</strong>
                            <span>Disable to pause manual and scheduled triggers.</span>
                          </div>
                          <input type="checkbox" checked={isEnabled} onChange={event => setIsEnabled(event.target.checked)} />
                        </label>
                        <label className="cf-auto-toggle-row full">
                          <div>
                            <strong>Require approval before execution</strong>
                            <span>Turn this off only for trusted workflows that may execute automatically through n8n.</span>
                          </div>
                          <input type="checkbox" checked={requiresApproval} onChange={event => setRequiresApproval(event.target.checked)} />
                        </label>
                      </div>
                    )
                  }

                  {
                    editorStep === 2
                    && (
                      <div className="cf-auto-choice-grid">
                        {ACTION_TYPES.map(type => (
                          <button
                            key={type}
                            type="button"
                            className={actionType === type ? "selected" : ""}
                            disabled={Boolean(editingAutomation)}
                            onClick={() => setActionType(type)}
                          >
                            <b>{actionIcon(type)}</b>
                            <strong>{actionLabel(type)}</strong>
                            <span>
                              {type === "email"
                                ? "Send through Gmail via n8n."
                                : type === "calendar"
                                  ? "Create a Google Calendar event."
                                  : "Call the allowlisted webhook."}
                            </span>
                          </button>
                        ))}
                      </div>
                    )
                  }

                  {
                    editorStep === 3
                    && (
                      <div>
                        <div className="cf-auto-trigger-grid">
                          {TRIGGER_TYPES.map(type => (
                            <button
                              key={type}
                              type="button"
                              className={triggerType === type ? "selected" : ""}
                              onClick={() => setTriggerType(type)}
                            >
                              <strong>{triggerLabel(type, null)}</strong>
                              <span>
                                {type === "manual" && "Run only when you click Run now."}
                                {type === "once" && "Trigger once at a future date/time."}
                                {type === "daily" && "Trigger every day at a fixed time."}
                                {type === "weekdays" && "Monday through Friday at a fixed time."}
                                {type === "weekly" && "One selected weekday every week."}
                                {type === "interval" && "Repeat every N hours from a start time."}
                              </span>
                            </button>
                          ))}
                        </div>

                        <div className="cf-auto-schedule-panel">
                          {
                            triggerType === "manual"
                            && (
                              <div className="cf-auto-locked-note">
                                <strong>Manual trigger</strong>
                                <span>No background schedule will be created.</span>
                              </div>
                            )
                          }

                          {
                            triggerType === "once"
                            && (
                              <div className="cf-auto-picker-wrap">
                                <div className="cf-auto-picker-heading">
                                  <div>
                                    <strong>Run at</strong>
                                    <span>Choose a date, then type any time. You can use 1:45, 1345 or 13:45.</span>
                                  </div>
                                  <small>Asia/Colombo (+05:30)</small>
                                </div>

                                <div className="cf-auto-picker-grid">
                                  <label className="cf-auto-picker-field">
                                    <span>Date</span>
                                    <div className="cf-auto-picker-control">
                                      <span className="cf-auto-picker-icon" aria-hidden="true">▦</span>
                                      <input
                                        className="cf-auto-date-input"
                                        type="date"
                                        value={onceDate}
                                        onChange={event => setOnceDate(event.target.value)}
                                      />
                                    </div>
                                  </label>

                                  <label className="cf-auto-picker-field">
                                    <span>Time</span>
                                    <div className="cf-auto-time-row">
                                      <div className="cf-auto-picker-control cf-auto-time-entry-control">
                                        <span className="cf-auto-picker-icon" aria-hidden="true">◷</span>
                                        <input
                                          className="cf-auto-time-input"
                                          type="text"
                                          inputMode="numeric"
                                          placeholder="1:55"
                                          value={onceTime}
                                          onChange={event => setOnceTime(event.target.value)}
                                          onBlur={() => {
                                            try {
                                              const parsed = parseFlexibleTime(
                                                onceTime,
                                                onceMeridiem
                                              );

                                              setOnceTime(parsed.time12);
                                              setOnceMeridiem(parsed.meridiem);
                                            } catch {
                                              // Keep the typed value so submit validation can show the error.
                                            }
                                          }}
                                          aria-label="Run time"
                                        />
                                      </div>

                                      <select
                                        className="cf-auto-meridiem-select"
                                        value={onceMeridiem}
                                        onChange={event => setOnceMeridiem(event.target.value as Meridiem)}
                                        aria-label="AM or PM"
                                      >
                                        <option value="AM">AM</option>
                                        <option value="PM">PM</option>
                                      </select>
                                    </div>
                                  </label>
                                </div>

                                <div className="cf-auto-picker-preview">
                                  <span>Selected schedule</span>
                                  <strong>
                                    {onceDate
                                      ? `${onceDate} at ${formatTwelveHourTime(onceTime, onceMeridiem)}`
                                      : "Choose a date to continue"}
                                  </strong>
                                </div>
                              </div>
                            )
                          }

                          {
                            (triggerType === "daily" || triggerType === "weekdays")
                            && (
                              <div className="cf-auto-form-grid">
                                <label>
                                  <span>Time</span>
                                  <input type="time" value={scheduleTime} onChange={event => setScheduleTime(event.target.value)} />
                                </label>
                                <label>
                                  <span>Timezone</span>
                                  <input value={scheduleTimezone} readOnly disabled />
                                </label>
                              </div>
                            )
                          }

                          {
                            triggerType === "weekly"
                            && (
                              <div className="cf-auto-form-grid">
                                <label>
                                  <span>Weekday</span>
                                  <select value={weeklyDay} onChange={event => setWeeklyDay(event.target.value)}>
                                    {WEEKDAYS.map(day => (
                                      <option key={day} value={day}>
                                        {day.charAt(0).toUpperCase() + day.slice(1)}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                                <label>
                                  <span>Time</span>
                                  <input type="time" value={scheduleTime} onChange={event => setScheduleTime(event.target.value)} />
                                </label>
                                <label className="full">
                                  <span>Timezone</span>
                                  <input value={scheduleTimezone} readOnly disabled />
                                </label>
                              </div>
                            )
                          }

                          {
                            triggerType === "interval"
                            && (
                              <div className="cf-auto-form-grid">
                                <label>
                                  <span>Every N hours</span>
                                  <input type="number" min="1" max="720" value={intervalHours} onChange={event => setIntervalHours(event.target.value)} />
                                </label>
                                <label>
                                  <span>Start at</span>
                                  <input type="datetime-local" value={intervalStart} onChange={event => setIntervalStart(event.target.value)} />
                                </label>
                              </div>
                            )
                          }

                          {
                            triggerType !== "manual"
                            && (
                              <div className={`cf-auto-safety-note ${requiresApproval ? "" : "auto"}`}>
                                <strong>{requiresApproval ? "Approval mode" : "Auto execution enabled"}</strong>
                                <p>
                                  {requiresApproval
                                    ? "When this schedule fires, ContextForge creates a pending ActionRequest. You must approve and execute it in Action Center."
                                    : "When this schedule fires, ContextForge immediately executes the action through n8n without waiting for Action Center approval. Use this only for trusted automations."}
                                </p>
                              </div>
                            )
                          }
                        </div>
                      </div>
                    )
                  }

                  {
                    editorStep === 4
                    && actionType === "email"
                    && (
                      <div className="cf-auto-form-grid">
                        <label className="full">
                          <span>Recipient</span>
                          <input type="email" value={emailTo} onChange={event => setEmailTo(event.target.value)} placeholder="client@example.com" />
                        </label>
                        <label className="full">
                          <span>Subject</span>
                          <input value={emailSubject} onChange={event => setEmailSubject(event.target.value)} placeholder="Project follow-up" />
                        </label>
                        <label className="full">
                          <span>Message</span>
                          <textarea value={emailBody} onChange={event => setEmailBody(event.target.value)} rows={8} placeholder="Email body" />
                        </label>
                      </div>
                    )
                  }

                  {
                    editorStep === 4
                    && actionType === "calendar"
                    && (
                      <div className="cf-auto-form-grid">
                        <label className="full">
                          <span>Event title</span>
                          <input value={calendarTitle} onChange={event => setCalendarTitle(event.target.value)} placeholder="Client meeting" />
                        </label>
                        <label>
                          <span>Start</span>
                          <input type="datetime-local" value={calendarStart} onChange={event => setCalendarStart(event.target.value)} />
                        </label>
                        <label>
                          <span>End</span>
                          <input type="datetime-local" value={calendarEnd} onChange={event => setCalendarEnd(event.target.value)} />
                        </label>
                        <label className="full">
                          <span>Timezone</span>
                          <input value={calendarTimezone} disabled readOnly />
                        </label>
                        <label className="full">
                          <span>Description</span>
                          <textarea value={calendarDescription} onChange={event => setCalendarDescription(event.target.value)} rows={5} />
                        </label>
                      </div>
                    )
                  }

                  {
                    editorStep === 4
                    && actionType === "webhook"
                    && (
                      <div className="cf-auto-form-grid">
                        <label className="full">
                          <span>Target</span>
                          <input value="demo_echo" disabled />
                          <small>Arbitrary outbound URLs remain blocked.</small>
                        </label>
                        <label className="full">
                          <span>JSON data</span>
                          <textarea className="code" value={webhookDataJson} onChange={event => setWebhookDataJson(event.target.value)} rows={10} />
                        </label>
                      </div>
                    )
                  }

                  {
                    editorStep === 5
                    && (
                      <div className="cf-auto-review">
                        <div>
                          <span>Name</span>
                          <strong>{name || "—"}</strong>
                        </div>
                        <div>
                          <span>Action</span>
                          <strong>{actionLabel(actionType)}</strong>
                        </div>
                        <div>
                          <span>Trigger</span>
                          <strong>{triggerLabel(triggerType, buildSchedule())}</strong>
                        </div>
                        <div>
                          <span>Execution mode</span>
                          <strong>{requiresApproval ? "Require approval" : "Auto execute"}</strong>
                        </div>
                        <div className="full">
                          <span>Execution behavior</span>
                          <p>
                            {requiresApproval
                              ? "Manual Run now or the background schedule creates a pending Action Center item. Nothing is sent or created externally until you approve and explicitly execute it."
                              : "Manual Run now and scheduled triggers execute immediately through n8n. The resulting action and run are still recorded for audit/history."}
                          </p>
                        </div>
                      </div>
                    )
                  }
                </div>

                <div className="cf-auto-modal-footer">
                  <button
                    type="button"
                    onClick={
                      editorStep === 1
                        ? closeEditor
                        : () => setEditorStep(previous => previous - 1)
                    }
                  >
                    {editorStep === 1 ? "Cancel" : "Back"}
                  </button>

                  {
                    editorStep < 5
                    ? (
                      <button
                        type="button"
                        className="primary"
                        onClick={() => validateStep(editorStep + 1)}
                      >
                        Continue
                      </button>
                    )
                    : (
                      <button type="submit" className="primary">
                        {editingAutomation ? "Save changes" : "Save automation"}
                      </button>
                    )
                  }
                </div>
              </form>
            </div>
          </div>
        )
      }
    </div>
  );
}
