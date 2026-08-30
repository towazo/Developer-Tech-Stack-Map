import UmapMap from "./UmapMap";

const patternColors = {
  A: "#f2c94c",
  B: "#56d6a4",
  C: "#ff6b8a",
};

export default function UmapMapSection({
  mapData,
  basePosition,
  patternPositions,
  neighborhoods,
}) {
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
            />
            <MapOverlayLegend />
          </div>

        </div>
      ) : (
        <p>マップデータを読み込んでいます...</p>
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
