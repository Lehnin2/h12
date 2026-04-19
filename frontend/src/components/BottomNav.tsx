import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { uiCopy } from "../lib/uiCopy";
import { useAppContext } from "../app/AppContext";
import { UiIcon } from "./UiIcon";

export function BottomNav() {
  const { profile, uiLanguage } = useAppContext();
  const copy = uiCopy[uiLanguage];
  const baseItems = [
    { to: "/", label: copy.nav.heatmap[0], hint: copy.nav.heatmap[1], icon: "heatmap" as const },
    { to: "/route", label: copy.nav.route[0], hint: copy.nav.route[1], icon: "route" as const },
    { to: "/lunar", label: copy.nav.lunar[0], hint: copy.nav.lunar[1], icon: "moon" as const },
    { to: "/safety", label: copy.nav.safety[0], hint: copy.nav.safety[1], icon: "safety" as const },
    { to: "/profile", label: copy.nav.profile[0], hint: copy.nav.profile[1], icon: "profile" as const },
  ];
  const items = profile?.is_admin
    ? [...baseItems, { to: "/admin", label: copy.nav.admin[0], hint: copy.nav.admin[1], icon: "admin" as const }]
    : baseItems;

  return (
    <nav className="bottom-nav" aria-label="Main navigation">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => `bottom-nav__item ${isActive ? "is-active" : ""}`}
        >
          <motion.span
            className="bottom-nav__icon-wrap"
            whileTap={{ scale: 0.9 }}
            whileHover={{ y: -2 }}
          >
            <UiIcon name={item.icon} duotone className="bottom-nav__icon" />
          </motion.span>
          <strong>{item.label}</strong>
          <span>{item.hint}</span>
        </NavLink>
      ))}
    </nav>
  );
}
