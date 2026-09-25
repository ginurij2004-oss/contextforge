type AICompanionProps = {
  variant?: "login" | "workspace" | "compact";
  label?: string;
};

export default function AICompanion({
  variant = "workspace",
  label,
}: AICompanionProps) {

  return (
    <div
      className={`cf-companion cf-companion-${variant}`}
      aria-hidden="true"
    >
      <div className="cf-companion-aura" />

      <div className="cf-companion-orbit cf-companion-orbit-one">
        <span />
      </div>

      <div className="cf-companion-orbit cf-companion-orbit-two">
        <span />
      </div>

      <div className="cf-companion-robot">
        <div className="cf-companion-antenna">
          <i />
        </div>

        <div className="cf-companion-head">
          <div className="cf-companion-visor">
            <span className="cf-companion-eye left" />
            <span className="cf-companion-eye right" />
            <span className="cf-companion-scan" />
          </div>
        </div>

        <div className="cf-companion-neck" />

        <div className="cf-companion-body">
          <div className="cf-companion-core">
            <img
              src="/contextforge-icon.png"
              alt=""
            />
          </div>

          <span className="cf-companion-body-line one" />
          <span className="cf-companion-body-line two" />
        </div>
      </div>

      <span className="cf-companion-particle p1" />
      <span className="cf-companion-particle p2" />
      <span className="cf-companion-particle p3" />

      {
        label
        && (
          <div className="cf-companion-label">
            <span className="cf-companion-live-dot" />
            {label}
          </div>
        )
      }
    </div>
  );
}
