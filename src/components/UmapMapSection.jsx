import { useMemo, useState } from "react";
import UmapMap from "./UmapMap";
import Footer from "./Footer";
import { translateMetadataValue } from "../utils/metadataTranslations";

const patternColors = {
  A: "#f2c94c",
  B: "#56d6a4",
  C: "#ff6b8a",
};
const respondentTrendColors = ["#4e79a7", "#f28e2c", "#59a14f", "#e15759", "#b07aa1"];
const otherTrendColor = "#76b7b2";
const missingTrendColor = "#cbd5e1";

export default function UmapMapSection({
  mapData,
  respondentMetadata,
  basePosition,
  patternPositions,
  neighborhoods,
}) {
  const [selectedMetadataKey, setSelectedMetadataKey] = useState("devType");
  const metadataTrend = useMemo(() => {
    if (
      !mapData?.points ||
      !respondentMetadata?.fields ||
      !respondentMetadata?.codesByRespondent
    ) {
      return null;
    }

    const fieldIndex = respondentMetadata.fields.findIndex(
      (field) => field.key === selectedMetadataKey
    );
    const safeFieldIndex = fieldIndex >= 0 ? fieldIndex : 0;
    const field = respondentMetadata.fields[safeFieldIndex];

    if (!field) {
      return null;
    }

    const counts = Array(field.values.length).fill(0);
    let answered = 0;
    let missing = 0;

    mapData.points.forEach((point) => {
      const code = respondentMetadata.codesByRespondent[point.id]?.[safeFieldIndex] ?? -1;

      if (code >= 0 && code < field.values.length) {
        counts[code] += 1;
        answered += 1;
      } else {
        missing += 1;
      }
    });

    const rankedItems = field.values
      .map((value, code) => ({
        code,
        value,
        count: counts[code],
        rate: answered ? counts[code] / answered * 100 : 0,
      }))
      .filter((item) => item.value !== "Other:" && item.count > 0)
      .sort((left, right) => right.count - left.count || left.value.localeCompare(right.value));

    const leadingItems = rankedItems.slice(0, 5).map((item, index) => ({
      ...item,
      label: translateMetadataValue(field.key, item.value),
      color: respondentTrendColors[index],
    }));
    const otherItems = rankedItems.slice(5);
    const otherCount = otherItems.reduce((total, item) => total + item.count, 0);
    const pointColorById = {};
    const codeToColor = new Map(
      leadingItems.map((item) => [item.code, item.color])
    );

    otherItems.forEach((item) => {
      codeToColor.set(item.code, otherTrendColor);
    });

    mapData.points.forEach((point) => {
      const code = respondentMetadata.codesByRespondent[point.id]?.[safeFieldIndex] ?? -1;
      pointColorById[point.id] = codeToColor.get(code) ?? missingTrendColor;
    });

    return {
      field,
      selectedKey: field.key,
      answered,
      missing,
      pointColorById,
      items: [
        ...leadingItems,
        ...(otherCount > 0
          ? [{
              label: "その他",
              count: otherCount,
              rate: answered ? otherCount / answered * 100 : 0,
              color: otherTrendColor,
            }]
          : []),
      ],
    };
  }, [mapData, respondentMetadata, selectedMetadataKey]);

  return (
    <div className="umap-map-section">
      {mapData ? (
        <div>
          <div className="umap-map-frame">
            <UmapMap
              points={mapData.points}
              basePosition={basePosition}
              patternPositions={patternPositions}
              neighborhoods={neighborhoods}
              pointColorById={metadataTrend?.pointColorById}
            />
            <div className="umap-map-overlay-stack">
              <MapOverlayLegend />
              <MapMetadataOverlay
                fields={respondentMetadata?.fields ?? []}
                selectedKey={metadataTrend?.selectedKey ?? selectedMetadataKey}
                trend={metadataTrend}
                onChange={setSelectedMetadataKey}
              />
            </div>
            <Footer />
          </div>

        </div>
      ) : (
        <p>マップデータを読み込んでいます...</p>
      )}
    </div>
  );
}

function MapMetadataOverlay({
  fields,
  selectedKey,
  trend,
  onChange,
}) {
  if (fields.length === 0) {
    return null;
  }

  return (
    <div className="umap-map-metadata-overlay">
      <label className="umap-map-metadata-label" htmlFor="map-metadata-select">
        回答者の傾向
      </label>
      <div className="select is-small">
        <select
          id="map-metadata-select"
          value={selectedKey}
          onChange={(event) => onChange(event.target.value)}
        >
          {fields.map((field) => (
            <option key={field.key} value={field.key}>
              {field.label}
            </option>
          ))}
        </select>
      </div>

      {trend && (
        <ul className="umap-map-metadata-legend">
          {trend.items.map((item) => (
            <li key={item.label}>
              <span
                className="umap-map-metadata-swatch"
                style={{ backgroundColor: item.color }}
                aria-hidden="true"
              />
              <span className="umap-map-metadata-name">{item.label}</span>
              <strong>{item.rate.toFixed(1)}%</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function MapOverlayLegend() {
  return (
    <div className="umap-map-overlay-legend" aria-label="マップの凡例">
      <strong className="umap-map-overlay-title">凡例</strong>

      <LegendRow
        graphic={<circle cx="22" cy="10" r="3" fill="#0a4bee" opacity="0.7" />}
        label="回答者"
      />
      <LegendRow
        graphic={<circle cx="22" cy="10" r="6" fill="#4cc9f0" stroke="#0f172a" strokeWidth="2" />}
        label="現在の技術"
      />
      <LegendRow
        graphic={
          <>
            <circle cx="8" cy="10" r="5" fill={patternColors.A} stroke="#334155" />
            <circle cx="22" cy="10" r="5" fill={patternColors.B} stroke="#334155" />
            <circle cx="36" cy="10" r="5" fill={patternColors.C} stroke="#334155" />
          </>
        }
        label="学習プラン A / B / C"
      />
      <LegendRow
        graphic={
          <circle
            cx="22"
            cy="10"
            r="8"
            fill="#4cc9f0"
            fillOpacity="0.12"
            stroke="#4cc9f0"
            strokeWidth="2"
            strokeDasharray="4 3"
          />
        }
        label="似ているエンジニア500人"
      />
      <LegendRow
        graphic={<line x1="4" y1="10" x2="40" y2="10" stroke={patternColors.A} strokeWidth="3" />}
        label="現在からの変化"
      />
    </div>
  );
}

function LegendRow({ graphic, label }) {
  return (
    <div className="umap-overlay-legend-row">
      <svg width="44" height="20" viewBox="0 0 44 20">
        {graphic}
      </svg>
      <span>{label}</span>
    </div>
  );
}
