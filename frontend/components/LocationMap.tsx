"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { useMemo } from "react";
import Map, { Layer, Marker, Source } from "react-map-gl/maplibre";

import type { LocationDetailResponse } from "@/lib/api-contract";

const ESRI_IMAGERY =
  "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

type Props = {
  detail: LocationDetailResponse;
};

export function LocationMap({ detail }: Props) {
  const { row, chosen_building } = detail;
  const lat = row.geocoded_lat ?? 39.8283;
  const lon = row.geocoded_lon ?? -98.5795;

  const footprintGeoJson = useMemo(() => {
    if (!chosen_building) return null;
    return {
      type: "FeatureCollection" as const,
      features: [
        {
          type: "Feature" as const,
          properties: { id: chosen_building.id },
          geometry: chosen_building.geometry,
        },
      ],
    };
  }, [chosen_building]);

  return (
    <div className="h-[420px] w-full overflow-hidden rounded border border-[var(--border)]">
      <Map
        initialViewState={{ latitude: lat, longitude: lon, zoom: 17 }}
        mapStyle={{
          version: 8,
          sources: {
            esri: {
              type: "raster",
              tiles: [ESRI_IMAGERY],
              tileSize: 256,
              attribution: "Esri World Imagery",
            },
          },
          layers: [{ id: "esri", type: "raster", source: "esri" }],
        }}
        style={{ width: "100%", height: "100%" }}
      >
        {footprintGeoJson ? (
          <Source id="footprint" type="geojson" data={footprintGeoJson}>
            <Layer
              id="footprint-fill"
              type="fill"
              paint={{ "fill-color": "#3b82f6", "fill-opacity": 0.35 }}
            />
            <Layer
              id="footprint-line"
              type="line"
              paint={{ "line-color": "#1d4ed8", "line-width": 2 }}
            />
          </Source>
        ) : null}
        <Marker latitude={lat} longitude={lon} color="#ef4444" />
      </Map>
    </div>
  );
}
