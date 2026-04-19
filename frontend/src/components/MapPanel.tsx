import { useEffect } from "react";
import { Circle, CircleMarker, LayersControl, MapContainer, Polyline, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { latLngBounds, type LatLngBoundsExpression, type LatLngExpression } from "leaflet";

import type { DeviceLocationSnapshot, RecommendationResponse, RouteResponse, ZoneCard } from "../types";
import type { UiLanguage } from "../lib/uiCopy";
import { recommendationLabel } from "../lib/uiLabels";

interface MapPanelProps {
  zones: ZoneCard[];
  recommendation: RecommendationResponse | null;
  route: RouteResponse | null;
  currentLocation: DeviceLocationSnapshot | null;
  uiLanguage: UiLanguage;
}

const GULF_BOUNDS: LatLngBoundsExpression = [
  [33.52, 9.95],
  [34.08, 10.68],
];

const GHANNOUCH_PLUME_CENTER: LatLngExpression = [33.952, 10.12];

function zoneStyle(color: ZoneCard["color"]) {
  switch (color) {
    case "GREEN":
      return { stroke: "#00BFA5", fill: "#00BFA5" };
    case "ORANGE":
      return { stroke: "#F5C26B", fill: "#F5C26B" };
    case "RED":
      return { stroke: "#E07A5F", fill: "#E07A5F" };
    default:
      return { stroke: "#1E3A5F", fill: "#1E3A5F" };
  }
}

function routeStateTone(state: string) {
  if (state === "TARGET") {
    return "#00BFA5";
  }
  if (state === "CAUTION") {
    return "#F5C26B";
  }
  return "#1E3A5F";
}

function FitToMission({
  zones,
  route,
  recommendation,
  currentLocation,
}: Omit<MapPanelProps, "uiLanguage">) {
  const map = useMap();

  useEffect(() => {
    const missionPoints: LatLngExpression[] = [];

    if (recommendation?.best_zone) {
      missionPoints.push([recommendation.best_zone.center_lat, recommendation.best_zone.center_lon]);
    }
    for (const zone of zones.slice(0, 5)) {
      missionPoints.push([zone.center_lat, zone.center_lon]);
    }
    for (const leg of route?.path ?? []) {
      missionPoints.push([leg.point.lat, leg.point.lon]);
    }
    if (currentLocation) {
      missionPoints.push([currentLocation.lat, currentLocation.lon]);
    }

    if (missionPoints.length >= 2) {
      map.fitBounds(latLngBounds(missionPoints), { padding: [32, 32] });
      return;
    }

    map.fitBounds(GULF_BOUNDS, { padding: [24, 24] });
  }, [currentLocation, map, recommendation, route, zones]);

  return null;
}

export function MapPanel({ zones, recommendation, route, currentLocation, uiLanguage }: MapPanelProps) {
  const bestId = recommendation?.best_zone.id;
  const routePoints: LatLngExpression[] = route?.path.map((leg) => [leg.point.lat, leg.point.lon]) ?? [];

  return (
    <div className="map-panel">
      {/* Operational overlays removed to clear redundant 'hero' text competition */}

      <div className="map-panel__canvas" role="img" aria-label="Operational marine map with live heat zones and route">
        <MapContainer
          className="map-panel__leaflet"
          bounds={GULF_BOUNDS}
          scrollWheelZoom
          zoomControl={false}
        >
          <FitToMission zones={zones} recommendation={recommendation} route={route} currentLocation={currentLocation} />

          <LayersControl position="bottomleft">
            <LayersControl.BaseLayer checked name="Mission basemap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
          </LayersControl>

          <Circle
            center={GHANNOUCH_PLUME_CENTER}
            radius={14500}
            pathOptions={{
              color: "#8C7AA8",
              fillColor: "#8C7AA8",
              fillOpacity: 0.12,
              weight: 2,
              dashArray: "8 8",
            }}
          >
            <Popup>
              <strong>Ghannouch plume corridor</strong>
              <div>Modeled industrial pollution buffer used by the recommendation engine.</div>
            </Popup>
          </Circle>

          {zones.map((zone) => {
            const style = zoneStyle(zone.color);
            const radius = zone.id === bestId ? 15 : Math.max(9, Math.round(zone.overall_score / 8));
            return (
              <CircleMarker
                key={zone.id}
                center={[zone.center_lat, zone.center_lon]}
                radius={radius}
                pathOptions={{
                  color: style.stroke,
                  fillColor: style.fill,
                  fillOpacity: zone.id === bestId ? 0.85 : 0.62,
                  weight: zone.id === bestId ? 3 : 1.5,
                }}
              >
                <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
                  <div className="map-panel__tooltip">
                    <strong>{zone.label}</strong>
                    <span>{zone.overall_score}/100 · {zone.color}</span>
                  </div>
                </Tooltip>
                <Popup>
                  <div className="map-panel__popup">
                    <strong>{zone.label}</strong>
                    <span>Score {zone.overall_score}/100 · {zone.color}</span>
                    <span>Pollution {zone.pollution_index}/100 · Boats {zone.active_boats}</span>
                    <span>Turbidity {zone.turbidity_fnu ?? "--"} FNU · Salinity {zone.salinity_psu ?? "--"} PSU</span>
                    <span>{zone.key_reason}</span>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {routePoints.length > 1 ? (
            <Polyline
              positions={routePoints}
              pathOptions={{
                color: "#1E3A5F",
                weight: 4,
                opacity: 0.7,
                dashArray: "10 8",
              }}
            />
          ) : null}

          {currentLocation ? (
            <>
              {currentLocation.accuracy_m && currentLocation.accuracy_m > 20 ? (
                <Circle
                  center={[currentLocation.lat, currentLocation.lon]}
                  radius={Math.min(currentLocation.accuracy_m, 1200)}
                  pathOptions={{
                    color: "#00BFA5",
                    fillColor: "#00BFA5",
                    fillOpacity: 0.08,
                    weight: 1.5,
                  }}
                />
              ) : null}
              <CircleMarker
                center={[currentLocation.lat, currentLocation.lon]}
                radius={9}
                pathOptions={{
                  color: "#FFFFFF",
                  fillColor: currentLocation.source === "live" ? "#00BFA5" : "#F5C26B",
                  fillOpacity: 1,
                  weight: 3,
                }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={0.96}>
                  <div className="map-panel__tooltip">
                    <strong>{currentLocation.source === "live" ? "Your live position" : "Last known position"}</strong>
                    <span>
                      {currentLocation.lat.toFixed(4)}, {currentLocation.lon.toFixed(4)}
                    </span>
                  </div>
                </Tooltip>
                <Popup>
                  <div className="map-panel__popup">
                    <strong>{currentLocation.source === "live" ? "Boat GPS fix" : "Cached boat position"}</strong>
                    <span>
                      Accuracy {currentLocation.accuracy_m == null ? "--" : `${Math.round(currentLocation.accuracy_m)} m`}
                    </span>
                    <span>
                      Speed {currentLocation.speed_kmh == null ? "--" : `${currentLocation.speed_kmh.toFixed(1)} km/h`}
                    </span>
                    <span>
                      Updated {new Date(currentLocation.captured_at).toLocaleTimeString()}
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            </>
          ) : null}

          {(route?.path ?? []).map((leg) => (
            <CircleMarker
              key={leg.label}
              center={[leg.point.lat, leg.point.lon]}
              radius={7}
              pathOptions={{
                color: routeStateTone(leg.safety_state),
                fillColor: routeStateTone(leg.safety_state),
                fillOpacity: 0.95,
                weight: 2,
              }}
            >
              <Tooltip direction="right" offset={[10, 0]} opacity={0.95}>
                <div className="map-panel__tooltip">
                  <strong>{leg.label}</strong>
                  <span>{leg.safety_state}</span>
                </div>
              </Tooltip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
