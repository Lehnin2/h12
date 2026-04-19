import { Navigate, NavLink, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useAppContext } from "./AppContext";

import { AuthScreen } from "../components/AuthScreen";
import { BottomNav } from "../components/BottomNav";
import { ChatAssistant } from "../components/ChatAssistant";
import { StatusPill } from "../components/StatusPill";
import { departureLabel } from "../lib/uiLabels";
import { uiCopy } from "../lib/uiCopy";

import { HeatmapPage } from "../pages/HeatmapPage";
import { RoutePage } from "../pages/RoutePage";
import { LunarPage } from "../pages/LunarPage";
import { SafetyPage } from "../pages/SafetyPage";
import { ProfilePage } from "../pages/ProfilePage";
import { AdminPage } from "../pages/AdminPage";

/* ── Shell Layout ───────────────────────────────────────────────── */

function AppShell() {
  const {
    token, profile, sessionLoading, isOnline,
    mission, deviceLocation, pendingSafetyQueue, uiLanguage, setUiLanguage,
    handleLogin, handleRegister,
  } = useAppContext();
  const { pathname } = useLocation();
  const copy = uiCopy[uiLanguage];
  const isHeatmapPage = pathname === "/";

  /* Session still loading → show loading state */
  if (sessionLoading) {
    return (
      <div className="shell shell--centered splash-screen">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ 
            duration: 0.8, 
            ease: [0.16, 1, 0.3, 1],
            repeat: Infinity,
            repeatType: "reverse" 
          }}
          className="splash-screen__logo"
        >
          <img src="/icons/icon-512.svg" alt="Guardian of the Gulf" />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="splash-screen__text"
        >
          <h1 className="font-display">Guardian of the Gulf</h1>
          <p>Chargement de votre mission...</p>
        </motion.div>
      </div>
    );
  }

  /* Not logged in → auth screen */
  if (!token || !profile) {
    return (
      <AuthScreen
        onLogin={handleLogin}
        onRegister={handleRegister}
      />
    );
  }

  /* Authenticated → full app */
  return (
    <div className="shell" dir={uiLanguage === "tn" ? "rtl" : "ltr"}>
      <div className="shell__statusbar shell__statusbar--top">
        <StatusPill tone={isOnline ? "good" : "warn"}>
          {isOnline ? copy.online : copy.offline}
        </StatusPill>
        <StatusPill tone="neutral">{profile.full_name}</StatusPill>
        <StatusPill tone="neutral">{mission?.selected_species?.replace("_", " ") ?? "Mission species"}</StatusPill>
        {deviceLocation ? (
          <StatusPill tone={deviceLocation.source === "live" ? "good" : "warn"}>
            {deviceLocation.source === "live" ? copy.gpsLive : copy.gpsCached}
          </StatusPill>
        ) : null}
        <div className="locale-switch" aria-label={copy.langLabel}>
          <button type="button" className={uiLanguage === "tn" ? "is-active" : ""} onClick={() => setUiLanguage("tn")}>عربي</button>
          <button type="button" className={uiLanguage === "fr" ? "is-active" : ""} onClick={() => setUiLanguage("fr")}>FR</button>
          <button type="button" className={uiLanguage === "en" ? "is-active" : ""} onClick={() => setUiLanguage("en")}>EN</button>
        </div>
      </div>

      {!isHeatmapPage && (
        <section className="mission-shell-card">
          <div className="mission-shell-card__copy">
            <h1>{copy.shellTitle}</h1>
          </div>
          <div className="mission-shell-card__signals">
            <div className="signal-chip">
              <span>{copy.departure}</span>
              <strong>{departureLabel(mission?.departure_decision?.status, uiLanguage)}</strong>
            </div>
            <div className="signal-chip">
              <span>{copy.port}</span>
              <strong>{mission?.departure_port ?? profile.home_port}</strong>
            </div>
          </div>
        </section>
      )}

      <main className="shell__main">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      <NavLink to="/safety" className="floating-sos" aria-label="Open safety controls">
        <span className="floating-sos__eyebrow">{copy.emergency}</span>
        <strong>SOS</strong>
      </NavLink>

      <ChatAssistant />

      <BottomNav />
    </div>
  );
}

function AdminRoute() {
  const { profile } = useAppContext();
  return profile?.is_admin ? <AdminPage /> : <Navigate to="/" replace />;
}

/* ── Router ──────────────────────────────────────────────────────── */

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HeatmapPage />} />
        <Route path="route" element={<RoutePage />} />
        <Route path="lunar" element={<LunarPage />} />
        <Route path="safety" element={<SafetyPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="admin" element={<AdminRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
