import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAppContext } from "../app/AppContext";
import { uiCopy } from "../lib/uiCopy";
import { UiIcon } from "./UiIcon";

import type {
  EmergencyContact,
  LoginPayload,
  RegisterPayload,
} from "../types";

interface AuthScreenProps {
  onLogin: (payload: LoginPayload) => Promise<void>;
  onRegister: (payload: RegisterPayload) => Promise<void>;
}

type Mode = "login" | "register";

const defaultContact: EmergencyContact = {
  name: "Haras Watani",
  phone: "+216-000-000",
  relation: "haras_watani",
};

export function AuthScreen({ onLogin, onRegister }: AuthScreenProps) {
  const { uiLanguage } = useAppContext();
  const copy = uiCopy[uiLanguage].auth;
  const [mode, setMode] = useState<Mode>("login");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loginState, setLoginState] = useState<LoginPayload>({
    email: "",
    password: "",
  });
  const [registerState, setRegisterState] = useState<RegisterPayload>({
    email: "",
    password: "",
    full_name: "",
    license_number: "",
    license_type: "artisanal",
    home_port: "zarrat",
    boat_name: "",
    boat_length_m: 8,
    engine_hp: 60,
    fuel_capacity_l: 50,
    fuel_consumption_l_per_hour: 8,
    fishing_gears: ["ligne"],
    target_species: ["poulpe"],
    emergency_contacts: [defaultContact],
  });

  const [registerStep, setRegisterStep] = useState(1);
  const totalSteps = 4;

  const title = useMemo(
    () => (mode === "login" ? copy.loginTitle : copy.registerTitle),
    [copy.loginTitle, copy.registerTitle, mode],
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "register" && registerStep < totalSteps) {
      setRegisterStep(s => s + 1);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") {
        await onLogin(loginState);
      } else {
        await onRegister(registerState);
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : copy.authError);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <section className="auth-hero">
        <p className="auth-hero__eyebrow">Guardian of the Gulf</p>
        <h1>{title}</h1>
        <p>{copy.hero}</p>
        <div className="auth-switch">
          <button
            className={mode === "login" ? "is-active" : ""}
            type="button"
            onClick={() => setMode("login")}
          >
            {copy.login}
          </button>
          <button
            className={mode === "register" ? "is-active" : ""}
            type="button"
            onClick={() => {
              setMode("register");
              setRegisterStep(1);
            }}
          >
            {copy.register}
          </button>
        </div>
      </section>

      <form className="auth-card" onSubmit={handleSubmit}>
        {mode === "register" && (
          <div className="auth-progress">
            <div className="auth-progress__bar">
              <div
                className="auth-progress__fill"
                style={{ width: `${(registerStep / totalSteps) * 100}%` }}
              />
            </div>
            <span>{copy.stepOf(registerStep, totalSteps)}</span>
          </div>
        )}

        {mode === "login" ? (
          <div className="auth-form-grid">
            <label>
              {copy.email}
              <input
                value={loginState.email}
                onChange={(event) =>
                  setLoginState((current) => ({ ...current, email: event.target.value }))
                }
                type="email"
                required
                placeholder="captain@guardian.gulf"
              />
            </label>
            <label>
              {copy.password}
              <input
                value={loginState.password}
                onChange={(event) =>
                  setLoginState((current) => ({ ...current, password: event.target.value }))
                }
                type="password"
                required
                placeholder="••••••••"
              />
            </label>
          </div>
        ) : (
          <div className="auth-form-grid auth-form-grid--wide">
            {registerStep === 1 && (
              <>
                <label>
                  {copy.fullName}
                  <input
                    value={registerState.full_name}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, full_name: event.target.value }))
                    }
                    type="text"
                    required
                  />
                </label>
                <label>
                  {copy.licenseType}
                  <select
                    value={registerState.license_type}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, license_type: event.target.value }))
                    }
                  >
                    <option value="artisanal">Artisanal</option>
                    <option value="côtier">Côtier</option>
                    <option value="hauturier">Hauturier</option>
                  </select>
                </label>
                <label>
                  {copy.homePort}
                  <select
                    value={registerState.home_port}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, home_port: event.target.value }))
                    }
                  >
                    <option value="zarrat">Zarrat</option>
                    <option value="ghannouch">Ghannouch</option>
                    <option value="teboulbou">Teboulbou</option>
                    <option value="oued_akarit">Oued Akarit</option>
                    <option value="mareth">Mareth</option>
                  </select>
                </label>
              </>
            )}

            {registerStep === 2 && (
              <>
                <label>
                  {copy.boatName}
                  <input
                    value={registerState.boat_name}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, boat_name: event.target.value }))
                    }
                    type="text"
                    required
                  />
                </label>
                <label>
                  {copy.boatLength}
                  <input
                    value={registerState.boat_length_m}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        boat_length_m: Number(event.target.value) || 0,
                      }))
                    }
                    type="number"
                    min="1"
                    step="0.1"
                  />
                </label>
                <label>
                  {copy.engineHp}
                  <input
                    value={registerState.engine_hp}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        engine_hp: Number(event.target.value) || 0,
                      }))
                    }
                    type="number"
                    min="1"
                  />
                </label>
              </>
            )}

            {registerStep === 3 && (
              <>
                <label>
                  {copy.fuelCapacity}
                  <input
                    value={registerState.fuel_capacity_l}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        fuel_capacity_l: Number(event.target.value) || 0,
                      }))
                    }
                    type="number"
                    min="1"
                    step="0.1"
                  />
                </label>
                <label>
                  {copy.fuelUse}
                  <input
                    value={registerState.fuel_consumption_l_per_hour}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        fuel_consumption_l_per_hour: Number(event.target.value) || 0,
                      }))
                    }
                    type="number"
                    min="0.1"
                    step="0.1"
                  />
                </label>
                <label>
                  {copy.fishingGears}
                  <input
                    value={registerState.fishing_gears.join(", ")}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        fishing_gears: event.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean),
                      }))
                    }
                    type="text"
                    placeholder="ligne, palangre, charfia"
                  />
                </label>
                <label>
                  {copy.targetSpecies}
                  <input
                    value={registerState.target_species.join(", ")}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        target_species: event.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean),
                      }))
                    }
                    type="text"
                    placeholder="poulpe, rouget"
                  />
                </label>
              </>
            )}

            {registerStep === 4 && (
              <>
                <label>
                  {copy.email}
                  <input
                    value={registerState.email}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, email: event.target.value }))
                    }
                    type="email"
                    required
                  />
                </label>
                <label>
                  {copy.password}
                  <input
                    value={registerState.password}
                    onChange={(event) =>
                      setRegisterState((current) => ({ ...current, password: event.target.value }))
                    }
                    type="password"
                    required
                  />
                </label>
                <label>
                  {copy.emergencyContactName}
                  <input
                    value={registerState.emergency_contacts[0]?.name ?? ""}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        emergency_contacts: [
                          {
                            ...(current.emergency_contacts[0] ?? defaultContact),
                            name: event.target.value,
                          },
                        ],
                      }))
                    }
                    type="text"
                    required
                  />
                </label>
                <label>
                  {copy.emergencyPhone}
                  <input
                    value={registerState.emergency_contacts[0]?.phone ?? ""}
                    onChange={(event) =>
                      setRegisterState((current) => ({
                        ...current,
                        emergency_contacts: [
                          {
                            ...(current.emergency_contacts[0] ?? defaultContact),
                            phone: event.target.value,
                          },
                        ],
                      }))
                    }
                    type="text"
                    required
                  />
                </label>
              </>
            )}
          </div>
        )}

        {error ? <p className="auth-error">{error}</p> : null}

        <div className="auth-actions">
          {mode === "register" && registerStep > 1 && (
            <button
              className="secondary-action"
              type="button"
              disabled={busy}
              onClick={() => setRegisterStep(s => s - 1)}
            >
              {copy.back}
            </button>
          )}
          <button className="auth-submit" type="submit" disabled={busy}>
            {busy ? copy.wait : (mode === "login" ? copy.openBoard : (registerStep === totalSteps ? copy.createProfile : copy.next))}
          </button>
        </div>
      </form>

      <div className="auth-extra">
        <motion.section
          className="landing-section"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <header className="landing-section__header">
            <h2>{copy.howItWorks.title}</h2>
            <p>{copy.howItWorks.subtitle}</p>
          </header>
          <div className="how-it-works-grid">
            <motion.div className="how-it-works-card" whileHover={{ y: -10 }}>
              <UiIcon name="satellite" duotone className="how-it-works-card__icon" />
              <strong>{copy.howItWorks.inputs.title}</strong>
              <span>{copy.howItWorks.inputs.body}</span>
            </motion.div>
            <motion.div className="how-it-works-card" whileHover={{ y: -10 }}>
              <UiIcon name="engine" duotone className="how-it-works-card__icon" />
              <strong>{copy.howItWorks.engine.title}</strong>
              <span>{copy.howItWorks.engine.body}</span>
            </motion.div>
            <motion.div className="how-it-works-card" whileHover={{ y: -10 }}>
              <UiIcon name="outputs" duotone className="how-it-works-card__icon" />
              <strong>{copy.howItWorks.outputs.title}</strong>
              <span>{copy.howItWorks.outputs.body}</span>
            </motion.div>
          </div>
        </motion.section>

        <motion.section
          className="landing-section"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <header className="landing-section__header">
            <h2>{copy.impact.title}</h2>
            <p>{copy.impact.subtitle}</p>
          </header>
          <div className="impact-grid">
            {copy.impact.cards.map((card, index) => (
              <motion.div
                key={card.title}
                className="impact-card"
                whileHover={{ scale: 1.02 }}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <UiIcon name={card.icon} duotone className="impact-card__icon" />
                <div className="impact-card__body">
                  <strong>{card.title}</strong>
                  <span>{card.body}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>
      </div>
    </div>
  );
}
