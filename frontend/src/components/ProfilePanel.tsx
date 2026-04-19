import { useMemo, useState } from "react";

import type { FishermanProfilePublic } from "../types";

interface ProfilePanelProps {
  profile: FishermanProfilePublic;
  onSave: (payload: Omit<FishermanProfilePublic, "id" | "email" | "is_admin">) => Promise<void>;
  onLogout: () => Promise<void>;
}

export function ProfilePanel({ profile, onSave, onLogout }: ProfilePanelProps) {
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [formState, setFormState] = useState({
    full_name: profile.full_name,
    license_number: profile.license_number ?? "",
    license_type: profile.license_type,
    home_port: profile.home_port,
    boat_name: profile.boat_name,
    boat_length_m: profile.boat_length_m,
    engine_hp: profile.engine_hp,
    fuel_capacity_l: profile.fuel_capacity_l,
    fuel_consumption_l_per_hour: profile.fuel_consumption_l_per_hour,
    fishing_gears: profile.fishing_gears.join(", "),
    target_species: profile.target_species.join(", "),
    emergency_name: profile.emergency_contacts[0]?.name ?? "",
    emergency_phone: profile.emergency_contacts[0]?.phone ?? "",
    emergency_relation: profile.emergency_contacts[0]?.relation ?? "haras_watani",
    avatar_url: profile.avatar_url ?? "",
  });

  const summary = useMemo(
    () =>
      `${profile.boat_name} · ${profile.license_type} · ${profile.home_port} · ${profile.target_species.join(", ")}`,
    [profile],
  );

  async function handleSave() {
    setBusy(true);
    try {
      await onSave({
        full_name: formState.full_name,
        license_number: formState.license_number || null,
        license_type: formState.license_type,
        home_port: formState.home_port,
        boat_name: formState.boat_name,
        boat_length_m: Number(formState.boat_length_m),
        engine_hp: Number(formState.engine_hp),
        fuel_capacity_l: Number(formState.fuel_capacity_l),
        fuel_consumption_l_per_hour: Number(formState.fuel_consumption_l_per_hour),
        fishing_gears: formState.fishing_gears.split(",").map((item) => item.trim()).filter(Boolean),
        target_species: formState.target_species.split(",").map((item) => item.trim()).filter(Boolean),
        emergency_contacts: [
          {
            name: formState.emergency_name,
            phone: formState.emergency_phone,
            relation: formState.emergency_relation,
          },
        ],
        avatar_url: formState.avatar_url || null,
      });
      setEditing(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="profile-panel">
      <div className="profile-panel__header">
        <div className="profile-avatar-container">
          <div className="profile-avatar">
            {profile.avatar_url ? (
              <img src={profile.avatar_url} alt={profile.full_name} />
            ) : (
              <div className="profile-avatar__placeholder">
                {profile.full_name.charAt(0).toUpperCase()}
              </div>
            )}
          </div>
        </div>
        <div className="profile-panel__info">
          <p className="section-card__eyebrow">Fisherman profile</p>
          <h3>{profile.full_name}</h3>
          <p>{summary}</p>
        </div>
        <div className="profile-panel__actions">
          <button type="button" onClick={() => setEditing((value) => !value)}>
            {editing ? "Close" : "Edit"}
          </button>
          <button type="button" onClick={() => void onLogout()}>
            Logout
          </button>
        </div>
      </div>

      {editing ? (
        <div className="profile-form-grid">
          <label>
            Full name
            <input
              value={formState.full_name}
              onChange={(event) => setFormState((current) => ({ ...current, full_name: event.target.value }))}
              type="text"
            />
          </label>
          <label>
            Home port
            <select
              value={formState.home_port}
              onChange={(event) => setFormState((current) => ({ ...current, home_port: event.target.value }))}
            >
              <option value="zarrat">Zarrat</option>
              <option value="ghannouch">Ghannouch</option>
              <option value="teboulbou">Teboulbou</option>
              <option value="oued_akarit">Oued Akarit</option>
              <option value="mareth">Mareth</option>
            </select>
          </label>
          <label>
            Boat name
            <input
              value={formState.boat_name}
              onChange={(event) => setFormState((current) => ({ ...current, boat_name: event.target.value }))}
              type="text"
            />
          </label>
          <label>
            Target species
            <input
              value={formState.target_species}
              onChange={(event) => setFormState((current) => ({ ...current, target_species: event.target.value }))}
              type="text"
            />
          </label>
          <label>
            Gears
            <input
              value={formState.fishing_gears}
              onChange={(event) => setFormState((current) => ({ ...current, fishing_gears: event.target.value }))}
              type="text"
            />
          </label>
          <label>
            Emergency phone
            <input
              value={formState.emergency_phone}
              onChange={(event) => setFormState((current) => ({ ...current, emergency_phone: event.target.value }))}
              type="text"
            />
          </label>
          <label>
            Avatar URL (Photo)
            <input
              value={formState.avatar_url}
              onChange={(event) => setFormState((current) => ({ ...current, avatar_url: event.target.value }))}
              type="url"
              placeholder="https://example.com/photo.jpg"
            />
          </label>
          <button className="profile-panel__save" type="button" onClick={() => void handleSave()} disabled={busy}>
            {busy ? "Saving..." : "Save mission profile"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
