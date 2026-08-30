import UmapMap from "./UmapMap";
import { clusterColors, clusterLabels } from "../config/clusters";

const patternColors = {
  A: "#ffdd57",
  B: "#48c78e",
  C: "#f14668",
};

export default function UmapMapSection({
  mapData,
  clusterData,
  basePosition,
  patternPositions,
  neighborhoods,
}) {
  return (
    <div className="umap-map-section">
      {mapData && clusterData ? (
        <div>
          <div className="umap-map-frame">
            <UmapMap
              points={mapData.points}
              clusters={clusterData.clusters}
              basePosition={basePosition}
              patternPositions={patternPositions}
              neighborhoods={neighborhoods}
            />
            <MapOverlayLegend clusters={clusterData.clusters} />
          </div>

        </div>
      ) : (
        <p>マップデータを読み込んでいます...</p>
      )}
    </div>
  );
}

function MapOverlayLegend({ clusters }) {
  return (
    <div className="umap-map-overlay-legend" aria-label="マップの凡例">
      <strong className="umap-map-overlay-title">凡例</strong>

      <div className="umap-cluster-legend">
        {clusters.map((cluster) => (
          <span key={cluster.id}>
            <i style={{ backgroundColor: clusterColors[cluster.id] }} />
            {clusterLabels[cluster.id]}
          </span>
        ))}
      </div>

      <LegendRow
        graphic={<circle cx="22" cy="10" r="3" fill="#64748b" opacity="0.7" />}
        label="回答者"
      />
      <LegendRow
        graphic={<circle cx="22" cy="10" r="6" fill="white" stroke="black" strokeWidth="2" />}
        label="Base"
      />
      <LegendRow
        graphic={
          <>
            <circle cx="8" cy="10" r="5" fill={patternColors.A} stroke="white" />
            <circle cx="22" cy="10" r="5" fill={patternColors.B} stroke="white" />
            <circle cx="36" cy="10" r="5" fill={patternColors.C} stroke="white" />
          </>
        }
        label="Pattern A / B / C"
      />
      <LegendRow
        graphic={
          <circle
            cx="22"
            cy="10"
            r="8"
            fill="#38bdf8"
            fillOpacity="0.12"
            stroke="#38bdf8"
            strokeWidth="2"
            strokeDasharray="4 3"
          />
        }
        label="近傍500人"
      />
      <LegendRow
        graphic={<line x1="4" y1="10" x2="40" y2="10" stroke={patternColors.A} strokeWidth="3" />}
        label="Baseからの変化"
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
