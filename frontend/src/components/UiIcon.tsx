import type { SVGProps } from "react";

type IconName =
  | "heatmap"
  | "route"
  | "moon"
  | "safety"
  | "profile"
  | "admin"
  | "catch"
  | "pollution"
  | "hazard"
  | "current"
  | "illegal"
  | "gps"
  | "contacts"
  | "queue"
  | "voice"
  | "chat"
  | "micro"
  | "close"
  | "satellite"
  | "engine"
  | "outputs"
  | "economic"
  | "environmental"
  | "public_health"
  | "territorial";

interface UiIconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  duotone?: boolean;
}

export function UiIcon({ name, duotone, className, ...props }: UiIconProps) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className: `ui-icon${className ? ` ${className}` : ""}${duotone ? " is-duotone" : ""}`,
    "aria-hidden": true,
    ...props,
  };

  const secondary = {
    stroke: "var(--accent-green)",
    strokeOpacity: 0.45,
    strokeWidth: 1.8,
  };

  switch (name) {
    case "heatmap":
      return (
        <svg {...common}>
          <path d="M4 15c1.5-5 4-8 8-9 2.5 3.5 4.8 6.5 8 8" />
          <path d="M4 19h16" />
          <circle cx="8" cy="14" r="1.5" {...(duotone ? secondary : {})} />
          <circle cx="13" cy="10" r="1.5" {...(duotone ? secondary : {})} />
          <circle cx="18" cy="14" r="1.5" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "route":
      return (
        <svg {...common}>
          <path d="M5 19c0-2.2 1.8-4 4-4h1a4 4 0 0 0 4-4V9" />
          <path d="M14 9h5" {...(duotone ? secondary : {})} />
          <path d="M16 6l3 3-3 3" {...(duotone ? secondary : {})} />
          <circle cx="6" cy="19" r="2" />
          <circle cx="14" cy="9" r="2" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "moon":
      return (
        <svg {...common}>
          <path d="M15 4a8 8 0 1 0 5 13.8A6.5 6.5 0 0 1 15 4z" />
          {duotone && <circle cx="12" cy="12" r="9" {...secondary} strokeDasharray="2 4" />}
        </svg>
      );
    case "safety":
      return (
        <svg {...common}>
          <path d="M12 3l7 3v5c0 4.5-2.7 8.3-7 10-4.3-1.7-7-5.5-7-10V6l7-3z" />
          <path d="M12 8v5" {...(duotone ? secondary : {})} />
          <path d="M12 16h.01" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "profile":
      return (
        <svg {...common}>
          <circle cx="12" cy="8" r="3.2" />
          <path d="M5.5 19a6.5 6.5 0 0 1 13 0" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "admin":
      return (
        <svg {...common}>
          <path d="M12 3l2.2 2.2 3.1-.4.9 3 2.8 1.4-1.4 2.8 1.4 2.8-2.8 1.4-.9 3-3.1-.4L12 21l-2.2-2.2-3.1.4-.9-3-2.8-1.4 1.4-2.8-1.4-2.8 2.8-1.4.9-3 3.1.4L12 3z" />
          <circle cx="12" cy="12" r="3" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "catch":
      return (
        <svg {...common}>
          <path d="M5 12c2-3 6-5 10-5 1.6 0 3 .3 4 1-1 3.2-4.5 6-8.5 6H8" />
          <path d="M5 12c0 3.3 2.7 6 6 6" {...(duotone ? secondary : {})} />
          <path d="M5 12H3" />
          <path d="M17 7l1.5-1.5" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "pollution":
      return (
        <svg {...common}>
          <path d="M7 18c0-2.2 1.8-4 4-4 0-2.2 1.8-4 4-4 1.7 0 3.2.8 4 2" />
          <path d="M4 18h16" />
          <path d="M8 8l2-4" {...(duotone ? secondary : {})} />
          <path d="M14 8l2-4" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "hazard":
      return (
        <svg {...common}>
          <path d="M12 4l8 14H4L12 4z" />
          <path d="M12 10v3.5" {...(duotone ? secondary : {})} />
          <path d="M12 16h.01" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "current":
      return (
        <svg {...common}>
          <path d="M4 9c2.5-2 5.5-2 8 0s5.5 2 8 0" />
          <path d="M4 15c2.5-2 5.5-2 8 0s5.5 2 8 0" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "illegal":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="M8.5 8.5l7 7" {...(duotone ? secondary : {})} />
          <path d="M15.5 8.5l-7 7" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "gps":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 3v3" {...(duotone ? secondary : {})} />
          <path d="M12 18v3" {...(duotone ? secondary : {})} />
          <path d="M3 12h3" {...(duotone ? secondary : {})} />
          <path d="M18 12h3" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "contacts":
      return (
        <svg {...common}>
          <path d="M7 18a4 4 0 0 1 8 0" />
          <circle cx="11" cy="9" r="3" {...(duotone ? secondary : {})} />
          <path d="M17 10h4" {...(duotone ? secondary : {})} />
          <path d="M19 8v4" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "queue":
      return (
        <svg {...common}>
          <path d="M4 7h12" />
          <path d="M4 12h9" />
          <path d="M4 17h6" />
          <path d="M17 15l3 3-3 3" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "voice":
      return (
        <svg {...common}>
          <path d="M12 6v12" />
          <path d="M9 9v6" {...(duotone ? secondary : {})} />
          <path d="M15 9v6" {...(duotone ? secondary : {})} />
          <path d="M5.5 9.5a7 7 0 0 0 0 5" />
          <path d="M18.5 9.5a7 7 0 0 1 0 5" />
        </svg>
      );
    case "chat":
      return (
        <svg {...common}>
          <path d="M6 18l-2 2V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6z" />
          <path d="M8 9h8" {...(duotone ? secondary : {})} />
          <path d="M8 13h5" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "micro":
      return (
        <svg {...common}>
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v1a7 7 0 0 1-14 0v-1" {...(duotone ? secondary : {})} />
          <line x1="12" y1="19" x2="12" y2="23" {...(duotone ? secondary : {})} />
          <line x1="8" y1="23" x2="16" y2="23" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "satellite":
      return (
        <svg {...common}>
          <path d="M3 7V5a2 2 0 0 1 2-2h2" />
          <path d="M17 3h2a2 2 0 0 1 2 2v2" />
          <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
          <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
          <circle cx="12" cy="12" r="3" />
          <path d="M12 9v1" {...(duotone ? secondary : {})} />
          <path d="M12 14v1" {...(duotone ? secondary : {})} />
          <path d="M9 12h1" {...(duotone ? secondary : {})} />
          <path d="M14 12h1" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "engine":
      return (
        <svg {...common}>
          <path d="M12 2v4" />
          <path d="M12 18v4" />
          <path d="M4.93 4.93l2.83 2.83" />
          <path d="M16.24 16.24l2.83 2.83" />
          <path d="M2 12h4" />
          <path d="M18 12h4" />
          <path d="M4.93 19.07l2.83-2.83" />
          <path d="M16.24 7.76l2.83-2.83" />
          <circle cx="12" cy="12" r="5" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "outputs":
      return (
        <svg {...common}>
          <path d="M21 12l-7-7v4H3v6h11v4z" />
          <path d="M18 8l3 4-3 4" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "economic":
      return (
        <svg {...common}>
          <path d="M12 2v20" />
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          <circle cx="12" cy="12" r="10" {...(duotone ? secondary : {})} strokeDasharray="4 4" />
        </svg>
      );
    case "environmental":
      return (
        <svg {...common}>
          <path d="M12 19c-2.3 0-6.4-1.9-6.4-8.2a6.4 6.4 0 1 1 12.8 0c0 6.3-4.1 8.2-6.4 8.2z" />
          <path d="M12 11c1 0 2 1.5 2 3s-1 3-2 3-2-1.5-2-3 1-3 2-3z" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "public_health":
      return (
        <svg {...common}>
          <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z" />
          <path d="M9 12h6" {...(duotone ? secondary : {})} />
          <path d="M12 9v6" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "territorial":
      return (
        <svg {...common}>
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
          <circle cx="12" cy="10" r="3" {...(duotone ? secondary : {})} />
        </svg>
      );
    case "close":
      return <svg {...common}><path d="M6 6l12 12" /><path d="M18 6L6 18" /></svg>;
    default:
      return <svg {...common}><circle cx="12" cy="12" r="8" /></svg>;
  }
}
