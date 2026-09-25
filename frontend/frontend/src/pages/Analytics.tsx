import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  getAnalyticsDashboard,
} from "../services/analytics";

import {
  useTheme,
} from "../theme/ThemeContext";

import {
  useAuth,
} from "../context/AuthContext";

import "./Analytics.css";


/* ==========================================================
   Types
========================================================== */

interface TrendPoint {
  label: string;
  value: number;
}


interface AnalyticsData {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;

  successRate: number;

  averageLatencyMs: number;

  inputTokens: number;
  outputTokens: number;
  totalTokens: number;

  generalRequests: number;
  documentRequests: number;
  agentRequests: number;

  requestTrend: TrendPoint[];
  latencyTrend: TrendPoint[];
}


/* ==========================================================
   Empty State
========================================================== */

const EMPTY_ANALYTICS: AnalyticsData = {
  totalRequests: 0,
  successfulRequests: 0,
  failedRequests: 0,

  successRate: 0,

  averageLatencyMs: 0,

  inputTokens: 0,
  outputTokens: 0,
  totalTokens: 0,

  generalRequests: 0,
  documentRequests: 0,
  agentRequests: 0,

  requestTrend: [],
  latencyTrend: [],
};


/* ==========================================================
   Analytics
========================================================== */

export default function Analytics() {

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
    data,
    setData,
  ] = useState<AnalyticsData>(
    EMPTY_ANALYTICS
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


  /* ========================================================
     Initial Load
  ======================================================== */

  useEffect(() => {

    loadAnalytics();

  }, []);


  /* ========================================================
     Load Analytics
  ======================================================== */

  const loadAnalytics =
    async (
      manual = false
    ) => {

      try {

        if (manual) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }


        setError("");


        const response =
          await getAnalyticsDashboard();


        const normalized =
          normalizeAnalytics(
            response
          );


        setData(
          normalized
        );


      } catch (error: any) {

        console.error(
          "ANALYTICS ERROR:",
          error
        );


        const detail =
          error?.response
            ?.data
            ?.detail;


        setError(
          detail
          || "Unable to load analytics."
        );


      } finally {

        setLoading(false);

        setRefreshing(false);

      }

    };


  /* ========================================================
     Sign Out
  ======================================================== */

  const handleLogout =
    () => {

      logout();

      navigate(
        "/login"
      );

    };


  /* ========================================================
     Derived Data
  ======================================================== */

  const averageLatencySeconds =
    data.averageLatencyMs
    / 1000;


  const requestBreakdown =
    useMemo(
      () => {

        return [
          {
            key: "general",
            label: "General AI",
            value:
              data.generalRequests,
            icon: "✦",
          },

          {
            key: "knowledge",
            label: "Knowledge",
            value:
              data.documentRequests,
            icon: "◫",
          },

          {
            key: "agent",
            label: "Agent",
            value:
              data.agentRequests,
            icon: "⚡",
          },
        ];

      },
      [data]
    );


  /* ========================================================
     Loading
  ======================================================== */

  if (
    loading
  ) {

    return (

      <div className="analytics-loading">

        <div className="analytics-loading-logo">
          C
        </div>

        <span>
          Loading analytics...
        </span>

      </div>

    );

  }


  /* ========================================================
     UI
  ======================================================== */

  return (

    <div className="analytics-shell">


      {/* =================================================
          Mobile Overlay
      ================================================= */}

      {
        mobileSidebarOpen
        && (

          <button
            type="button"

            className="analytics-mobile-overlay"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }

            aria-label="Close menu"
          />

        )
      }


      {/* =================================================
          Sidebar
      ================================================= */}

      <aside
        className={
          mobileSidebarOpen
          ? "analytics-sidebar open"
          : "analytics-sidebar"
        }
      >


        <div className="analytics-brand">


          <div className="analytics-logo">

            C

          </div>


          <div>

            <strong>
              ContextForge
            </strong>

            <span>
              Enterprise AI
            </span>

          </div>


          <button
            type="button"

            className="analytics-sidebar-close"

            onClick={() =>
              setMobileSidebarOpen(
                false
              )
            }
          >
            ×
          </button>


        </div>


        {/* Navigation */}

        <nav className="analytics-navigation">


          <button
            type="button"

            onClick={() =>
              navigate(
                "/"
              )
            }
          >

            <span>
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

            <span>
              ◫
            </span>

            Documents

          </button>


          <button
            type="button"

            className="active"
          >

            <span>
              ◩
            </span>

            Analytics

          </button>


        </nav>


        {/* Sidebar Insight */}

        <div className="analytics-sidebar-insight">


          <span className="analytics-sidebar-label">

            Workspace health

          </span>


          <div className="analytics-health-row">


            <span className="analytics-health-dot" />


            <div>

              <strong>
                Operational
              </strong>

              <span>
                AI services responding
              </span>

            </div>


          </div>


        </div>


        {/* Sidebar Footer */}

        <div className="analytics-sidebar-footer">


          <div className="analytics-online">

            <span />

            ContextForge online

          </div>


          <button
            type="button"

            onClick={
              handleLogout
            }
          >

            ↗ Sign out

          </button>


        </div>


      </aside>


      {/* =================================================
          Main
      ================================================= */}

      <main className="analytics-main">


        {/* =================================================
            Header
        ================================================= */}

        <header className="analytics-header">


          <div className="analytics-header-main">


            <button
              type="button"

              className="analytics-mobile-menu"

              onClick={() =>
                setMobileSidebarOpen(
                  true
                )
              }
            >
              ☰
            </button>


            <div>

              <span className="analytics-eyebrow">

                Intelligence

              </span>


              <h1>
                Analytics
              </h1>


              <p>

                Monitor AI performance,
                usage and knowledge quality.

              </p>

            </div>


          </div>


          <div className="analytics-header-actions">


            <button
              type="button"

              className="analytics-refresh"

              disabled={
                refreshing
              }

              onClick={() =>
                loadAnalytics(
                  true
                )
              }
            >

              <span
                className={
                  refreshing
                  ? "spin"
                  : ""
                }
              >
                ↻
              </span>

              {
                refreshing
                ? "Refreshing"
                : "Refresh"
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


        {/* =================================================
            Scrollable Content
        ================================================= */}

        <div className="analytics-content">


          {/* Error */}

          {
            error
            && (

              <div className="analytics-error">

                <strong>
                  !
                </strong>

                {
                  error
                }

              </div>

            )
          }


          {/* =================================================
              Overview Heading
          ================================================= */}

          <section className="analytics-section-intro">


            <div>

              <span>
                Overview
              </span>

              <h2>
                Workspace performance
              </h2>

            </div>


            <div className="analytics-period">

              <span className="analytics-period-dot" />

              Current data

            </div>


          </section>


          {/* =================================================
              KPI Cards
          ================================================= */}

          <section className="analytics-kpi-grid">


            <MetricCard
              icon="↗"
              label="Total requests"
              value={
                formatNumber(
                  data.totalRequests
                )
              }
              helper="All AI interactions"
              tone="purple"
            />


            <MetricCard
              icon="✓"
              label="Success rate"
              value={
                `${data.successRate.toFixed(1)}%`
              }
              helper={
                (
                  `${formatNumber(
                    data.successfulRequests
                  )} successful`
                )
              }
              tone="green"
            />


            <MetricCard
              icon="◷"
              label="Average latency"
              value={
                `${averageLatencySeconds.toFixed(2)}s`
              }
              helper="Average response time"
              tone="blue"
            />


            <MetricCard
              icon="◇"
              label="Tokens used"
              value={
                formatCompact(
                  data.totalTokens
                )
              }
              helper={
                (
                  `${formatCompact(
                    data.inputTokens
                  )} in · `
                  + `${formatCompact(
                    data.outputTokens
                  )} out`
                )
              }
              tone="orange"
            />


          </section>


          {/* =================================================
              Charts
          ================================================= */}

          <section className="analytics-chart-grid">


            <AnalyticsPanel
              title="Request activity"
              description="AI requests over time"
              badge="Requests"
            >

              <RequestBarChart
                points={
                  data.requestTrend
                }
              />

            </AnalyticsPanel>


            <AnalyticsPanel
              title="Response latency"
              description="Average response time"
              badge="Milliseconds"
            >

              <LatencyLineChart
                points={
                  data.latencyTrend
                }
              />

            </AnalyticsPanel>


          </section>


          {/* =================================================
              Request Breakdown
          ================================================= */}

          <section className="analytics-bottom-grid">


            <AnalyticsPanel
              title="Request breakdown"
              description="How your workspace is being used"
            >

              <RequestBreakdown
                items={
                  requestBreakdown
                }

                total={
                  data.totalRequests
                }
              />

            </AnalyticsPanel>


            <AnalyticsPanel
              title="System summary"
              description="Current operational metrics"
            >

              <div className="analytics-summary-list">


                <SummaryRow
                  label="Successful requests"
                  value={
                    formatNumber(
                      data.successfulRequests
                    )
                  }
                  indicator="good"
                />


                <SummaryRow
                  label="Failed requests"
                  value={
                    formatNumber(
                      data.failedRequests
                    )
                  }
                  indicator={
                    data.failedRequests > 0
                    ? "warning"
                    : "good"
                  }
                />


                <SummaryRow
                  label="Input tokens"
                  value={
                    formatNumber(
                      data.inputTokens
                    )
                  }
                />


                <SummaryRow
                  label="Output tokens"
                  value={
                    formatNumber(
                      data.outputTokens
                    )
                  }
                />


                <SummaryRow
                  label="Knowledge requests"
                  value={
                    formatNumber(
                      data.documentRequests
                    )
                  }
                />


                <SummaryRow
                  label="Agent requests"
                  value={
                    formatNumber(
                      data.agentRequests
                    )
                  }
                />


              </div>

            </AnalyticsPanel>


          </section>


        </div>


      </main>


    </div>

  );

}


/* ==========================================================
   Metric Card
========================================================== */

function MetricCard({
  icon,
  label,
  value,
  helper,
  tone,
}: {
  icon: string;
  label: string;
  value: string;
  helper: string;
  tone:
    | "purple"
    | "green"
    | "blue"
    | "orange";
}) {

  return (

    <article
      className={
        `analytics-metric ${tone}`
      }
    >


      <div className="analytics-metric-top">


        <div className="analytics-metric-icon">

          {
            icon
          }

        </div>


        <span>
          {
            label
          }
        </span>


      </div>


      <strong className="analytics-metric-value">

        {
          value
        }

      </strong>


      <span className="analytics-metric-helper">

        {
          helper
        }

      </span>


    </article>

  );

}


/* ==========================================================
   Generic Panel
========================================================== */

function AnalyticsPanel({
  title,
  description,
  badge,
  children,
}: {
  title: string;
  description: string;
  badge?: string;
  children: React.ReactNode;
}) {

  return (

    <article className="analytics-panel">


      <div className="analytics-panel-header">


        <div>

          <h3>
            {
              title
            }
          </h3>

          <p>
            {
              description
            }
          </p>

        </div>


        {
          badge
          && (

            <span className="analytics-panel-badge">

              {
                badge
              }

            </span>

          )
        }


      </div>


      <div className="analytics-panel-body">

        {
          children
        }

      </div>


    </article>

  );

}


/* ==========================================================
   Bar Chart
========================================================== */

function RequestBarChart({
  points,
}: {
  points: TrendPoint[];
}) {

  if (
    points.length === 0
  ) {

    return (
      <ChartEmpty />
    );

  }


  const maxValue =
    Math.max(
      ...points.map(
        (
          point
        ) =>
          point.value
      ),
      1
    );


  return (

    <div className="analytics-bar-chart">


      <div className="analytics-bar-area">


        {
          points.map(
            (
              point,
              index
            ) => {

              const percentage =
                Math.max(
                  (
                    point.value
                    / maxValue
                  )
                  * 100,
                  point.value > 0
                    ? 5
                    : 0
                );


              return (

                <div
                  className="analytics-bar-column"

                  key={
                    `${point.label}-${index}`
                  }
                >


                  <div className="analytics-bar-value">

                    {
                      formatCompact(
                        point.value
                      )
                    }

                  </div>


                  <div className="analytics-bar-track">

                    <div
                      className="analytics-bar-fill"

                      style={{
                        height:
                          `${percentage}%`,
                      }}
                    />

                  </div>


                  <span>

                    {
                      point.label
                    }

                  </span>


                </div>

              );

            }
          )
        }


      </div>


    </div>

  );

}


/* ==========================================================
   SVG Line Chart
========================================================== */

function LatencyLineChart({
  points,
}: {
  points: TrendPoint[];
}) {

  if (
    points.length === 0
  ) {

    return (
      <ChartEmpty />
    );

  }


  const width = 720;
  const height = 250;

  const horizontalPadding = 28;
  const topPadding = 22;
  const bottomPadding = 34;


  const maxValue =
    Math.max(
      ...points.map(
        (
          point
        ) =>
          point.value
      ),
      1
    );


  const chartHeight =
    height
    - topPadding
    - bottomPadding;


  const chartWidth =
    width
    - horizontalPadding * 2;


  const coordinates =
    points.map(
      (
        point,
        index
      ) => {

        const x =
          horizontalPadding
          +
          (
            points.length === 1
            ? chartWidth / 2
            : (
                index
                / (
                    points.length
                    - 1
                  )
              )
              * chartWidth
          );


        const y =
          topPadding
          +
          chartHeight
          -
          (
            point.value
            / maxValue
          )
          * chartHeight;


        return {
          x,
          y,
        };

      }
    );


  const polyline =
    coordinates
      .map(
        (
          point
        ) =>
          `${point.x},${point.y}`
      )
      .join(
        " "
      );


  const areaPath =
    (
      `M ${coordinates[0].x} `
      + `${height - bottomPadding} `
      + `L ${polyline.replaceAll(
        ",",
        " "
      )} `
      + `L ${
          coordinates[
            coordinates.length - 1
          ].x
        } `
      + `${height - bottomPadding} Z`
    );


  return (

    <div className="analytics-line-chart">


      <svg
        viewBox={
          `0 0 ${width} ${height}`
        }

        preserveAspectRatio="none"
      >


        <defs>

          <linearGradient
            id="analyticsLatencyArea"
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >

            <stop
              offset="0%"
              stopColor="currentColor"
              stopOpacity="0.25"
            />

            <stop
              offset="100%"
              stopColor="currentColor"
              stopOpacity="0"
            />

          </linearGradient>

        </defs>


        {/* Grid */}

        {
          [0, 1, 2, 3].map(
            (
              index
            ) => {

              const y =
                topPadding
                +
                (
                  chartHeight
                  / 3
                )
                * index;


              return (

                <line
                  key={
                    index
                  }

                  x1={
                    horizontalPadding
                  }

                  x2={
                    width
                    - horizontalPadding
                  }

                  y1={
                    y
                  }

                  y2={
                    y
                  }

                  className="analytics-chart-grid-line"
                />

              );

            }
          )
        }


        <path
          d={
            areaPath
          }

          className="analytics-area-fill"
        />


        <polyline
          points={
            polyline
          }

          className="analytics-latency-line"
        />


        {
          coordinates.map(
            (
              coordinate,
              index
            ) => (

              <circle
                key={
                  index
                }

                cx={
                  coordinate.x
                }

                cy={
                  coordinate.y
                }

                r="5"

                className="analytics-line-dot"
              />

            )
          )
        }


      </svg>


      <div className="analytics-line-labels">


        {
          points.map(
            (
              point,
              index
            ) => (

              <span
                key={
                  `${point.label}-${index}`
                }
              >

                {
                  point.label
                }

              </span>

            )
          )
        }


      </div>


    </div>

  );

}


/* ==========================================================
   Breakdown
========================================================== */

function RequestBreakdown({
  items,
  total,
}: {
  items: {
    key: string;
    label: string;
    value: number;
    icon: string;
  }[];
  total: number;
}) {

  return (

    <div className="analytics-breakdown">


      {/* Donut */}

      <div className="analytics-donut-wrapper">


        <div
          className="analytics-donut"

          style={{
            background:
              buildDonutGradient(
                items,
                total
              ),
          }}
        >


          <div className="analytics-donut-center">

            <strong>

              {
                formatCompact(
                  total
                )
              }

            </strong>

            <span>
              Total
            </span>

          </div>


        </div>


      </div>


      {/* Legend */}

      <div className="analytics-breakdown-legend">


        {
          items.map(
            (
              item
            ) => {

              const percentage =
                total > 0
                ? (
                    item.value
                    / total
                  )
                  * 100
                : 0;


              return (

                <div
                  className={
                    (
                      "analytics-legend-row "
                      + item.key
                    )
                  }

                  key={
                    item.key
                  }
                >


                  <div className="analytics-legend-icon">

                    {
                      item.icon
                    }

                  </div>


                  <div className="analytics-legend-name">

                    <strong>

                      {
                        item.label
                      }

                    </strong>

                    <span>

                      {
                        percentage.toFixed(
                          1
                        )
                      }
                      % of requests

                    </span>

                  </div>


                  <strong className="analytics-legend-value">

                    {
                      formatNumber(
                        item.value
                      )
                    }

                  </strong>


                </div>

              );

            }
          )
        }


      </div>


    </div>

  );

}


/* ==========================================================
   Summary Row
========================================================== */

function SummaryRow({
  label,
  value,
  indicator,
}: {
  label: string;
  value: string;
  indicator?:
    | "good"
    | "warning";
}) {

  return (

    <div className="analytics-summary-row">


      <div>


        {
          indicator
          && (

            <span
              className={
                (
                  "analytics-summary-indicator "
                  + indicator
                )
              }
            />

          )
        }


        <span>
          {
            label
          }
        </span>


      </div>


      <strong>

        {
          value
        }

      </strong>


    </div>

  );

}


/* ==========================================================
   Empty Chart
========================================================== */

function ChartEmpty() {

  return (

    <div className="analytics-chart-empty">

      <div>
        ◌
      </div>

      <strong>
        No trend data yet
      </strong>

      <span>
        More activity is needed before
        this chart can be displayed.
      </span>

    </div>

  );

}


/* ==========================================================
   API Normalization
========================================================== */

function normalizeAnalytics(
  raw: any
): AnalyticsData {

  const overview =
    raw?.overview
    ?? raw
    ?? {};


  const dailyActivity =
    Array.isArray(
      raw?.daily_activity
    )
      ? raw.daily_activity
      : [];


  const totalRequests =
    numberValue(
      overview?.total_requests,
      overview?.totalRequests,
      overview?.ai_requests,
      overview?.request_count
    );


  const successfulRequests =
    numberValue(
      overview?.successful_requests,
      overview?.successfulRequests,
      overview?.success_count
    );


  const failedRequests =
    numberValue(
      overview?.failed_requests,
      overview?.failedRequests,
      overview?.failure_count,
      Math.max(
        totalRequests
        - successfulRequests,
        0
      )
    );


  const successRateRaw =
    numberValue(
      overview?.success_rate,
      overview?.successRate
    );


  const successRate =
    successRateRaw > 0
      ? successRateRaw
      : (
          totalRequests > 0
            ? (
                successfulRequests
                / totalRequests
              )
              * 100
            : 0
        );


  const averageLatencyMs =
    numberValue(
      overview?.average_latency_ms,
      overview?.avg_latency_ms,
      overview?.averageLatencyMs,
      overview?.latency_ms
    );


  const inputTokens =
    numberValue(
      overview?.total_input_tokens,
      overview?.input_tokens,
      overview?.inputTokens
    );


  const outputTokens =
    numberValue(
      overview?.total_output_tokens,
      overview?.output_tokens,
      overview?.outputTokens
    );


  const totalTokens =
    numberValue(
      overview?.total_tokens,
      overview?.totalTokens,
      inputTokens + outputTokens
    );


  const generalRequests =
    numberValue(
      overview?.chat_requests,
      overview?.general_ai_requests,
      overview?.general_requests,
      overview?.generalRequests
    );


  const documentRequests =
    numberValue(
      overview?.document_requests,
      overview?.rag_requests,
      overview?.knowledge_requests,
      overview?.documentRequests
    );


  const agentRequests =
    numberValue(
      overview?.agent_requests,
      overview?.agentRequests
    );


  return {

    totalRequests,

    successfulRequests,

    failedRequests,

    successRate,

    averageLatencyMs,

    inputTokens,

    outputTokens,

    totalTokens,

    generalRequests,

    documentRequests,

    agentRequests,

    requestTrend:
      normalizeTrend(
        dailyActivity.length > 0
          ? dailyActivity
          : (
              raw?.requests_by_day
              ?? raw?.request_trend
              ?? raw?.requests_last_7_days
              ?? raw?.daily_requests
            )
      ),

    latencyTrend:
      normalizeTrend(
        dailyActivity.length > 0
          ? dailyActivity
          : (
              raw?.latency_by_day
              ?? raw?.latency_trend
              ?? raw?.latency_last_7_days
              ?? raw?.daily_latency
            ),
        true
      ),
  };

}


/* ==========================================================
   Trend Normalizer
========================================================== */

function normalizeTrend(
  raw: any,
  latency = false
): TrendPoint[] {

  if (
    !Array.isArray(
      raw
    )
  ) {

    return [];

  }


  return raw.map(
    (
      item,
      index
    ) => {

      if (
        typeof item === "number"
      ) {

        return {
          label:
            `Day ${index + 1}`,
          value:
            item,
        };

      }


      return {

        label:
          formatTrendLabel(
            item?.label
            ?? item?.date
            ?? item?.day
            ?? item?.name
            ?? `Day ${index + 1}`
          ),

        value:
          numberValue(
            item?.value,

            latency
              ? item?.average_latency_ms
              : item?.count,

            latency
              ? item?.latency_ms
              : item?.requests,

            item?.total
          ),
      };

    }
  );

}


/* ==========================================================
   Helpers
========================================================== */

function numberValue(
  ...values: any[]
): number {

  for (
    const value
    of values
  ) {

    const converted =
      Number(
        value
      );


    if (
      Number.isFinite(
        converted
      )
    ) {

      return converted;

    }

  }


  return 0;

}


function formatNumber(
  value: number
) {

  return new Intl.NumberFormat(
    "en-US"
  ).format(
    Math.round(
      value
    )
  );

}


function formatCompact(
  value: number
) {

  return new Intl.NumberFormat(
    "en-US",
    {
      notation: "compact",
      maximumFractionDigits: 1,
    }
  ).format(
    value
  );

}


function formatTrendLabel(
  value: string
) {

  const date =
    new Date(
      value
    );


  if (
    !Number.isNaN(
      date.getTime()
    )

    &&

    value.includes(
      "-"
    )
  ) {

    return date.toLocaleDateString(
      "en-US",
      {
        month: "short",
        day: "numeric",
      }
    );

  }


  return String(
    value
  );

}


/* ==========================================================
   Donut
========================================================== */

function buildDonutGradient(
  items: {
    value: number;
  }[],
  total: number
) {

  if (
    total <= 0
  ) {

    return (
      "conic-gradient("
      + "var(--border-strong) 0deg 360deg"
      + ")"
    );

  }


  const colors = [
    "#7567ff",
    "#28a9e8",
    "#f59e5b",
  ];


  let current = 0;


  const segments =
    items.map(
      (
        item,
        index
      ) => {

        const start =
          current;


        const degrees =
          (
            item.value
            / total
          )
          * 360;


        current +=
          degrees;


        return (
          `${colors[index]} `
          + `${start}deg `
          + `${current}deg`
        );

      }
    );


  return (
    `conic-gradient(${segments.join(",")})`
  );

}