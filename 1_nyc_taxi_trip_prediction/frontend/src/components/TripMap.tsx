import { useEffect, useState } from "react";
import { MapContainer, Marker, Polyline, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import type { LatLng } from "../types";

const pickupIcon = new L.DivIcon({
  className: "pin pickup-pin",
  html: "<span>P</span>",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const dropoffIcon = new L.DivIcon({
  className: "pin dropoff-pin",
  html: "<span>D</span>",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

type Props = {
  pickup: LatLng | null;
  dropoff: LatLng | null;
  selecting: "pickup" | "dropoff";
  onMapClick: (point: LatLng) => void;
};

function ClickHandler({ onMapClick }: { onMapClick: (point: LatLng) => void }) {
  useMapEvents({
    click(e) {
      onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

export function TripMap({ pickup, dropoff, selecting, onMapClick }: Props) {
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);

  if (!ready) return <div className="map-placeholder">Loading map…</div>;

  return (
    <div className="map-shell" aria-label={`Click map to set ${selecting} location`}>
      <MapContainer
        center={[40.758, -73.9855]}
        zoom={12}
        className="map"
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickHandler onMapClick={onMapClick} />
        {pickup && <Marker position={[pickup.lat, pickup.lng]} icon={pickupIcon} />}
        {dropoff && <Marker position={[dropoff.lat, dropoff.lng]} icon={dropoffIcon} />}
        {pickup && dropoff && (
          <Polyline
            positions={[
              [pickup.lat, pickup.lng],
              [dropoff.lat, dropoff.lng],
            ]}
            pathOptions={{ color: "#1d4ed8", weight: 3, dashArray: "6 8" }}
          />
        )}
      </MapContainer>
      <p className="map-hint" role="status">
        Click to set <strong>{selecting}</strong> point
        {pickup && dropoff ? " · both points set" : ""}
      </p>
    </div>
  );
}
