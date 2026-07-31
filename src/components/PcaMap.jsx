import { useState } from "react";
import * as d3 from "d3";

export default function PcaMap({
  points,
  clusters,
  basePosition,
  patternPositions,
}) {
  const width = 900;
  const height = 600;

  // 現在ラベルを表示している要素を管理する
  const [visibleLabels, setVisibleLabels] = useState(new Set());

  // ラベルの表示・非表示を切り替える
  const toggleLabel = (labelKey) => {
    setVisibleLabels((currentLabels) => {
      const nextLabels = new Set(currentLabels);

      if (nextLabels.has(labelKey)) {
        nextLabels.delete(labelKey);
      } else {
        nextLabels.add(labelKey);
      }

      return nextLabels;
    });
  };

  const margin = {
    top: 30,
    right: 30,
    bottom: 50,
    left: 60,
  };

  // PCAのx座標の最小値・最大値
  const xExtent = d3.extent(points, (point) => point.x);

  // PCAのy座標の最小値・最大値
  const yExtent = d3.extent(points, (point) => point.y);

  const xScale = d3
    .scaleLinear()
    .domain([xExtent[0], xExtent[1]])
    .range([margin.left, width - margin.right]);

  const yScale = d3
    .scaleLinear()
    .domain([yExtent[0], yExtent[1]])
    .range([height - margin.bottom, margin.top]);

  // schemeTableau10はd3で用意された色配列
  const colorScale = d3
    .scaleOrdinal()
    .domain([0, 1, 2, 3, 4, 5])
    .range(d3.schemeTableau10.slice(0, 6));

  const adjustment = {
    0: { x: 20, y: 5 },
    1: { x: 15, y: -8 },
    2: { x: 20, y: 5 },
    3: { x: 20, y: 5 },
    4: { x: 20, y: 5 },
    5: { x: 20, y: 5 },
  };

  const patternColors = {
    A: "#ffdd57",
    B: "#48c78e",
    C: "#f14668",
  };

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{
        width: "100%",
        height: "auto",
      }}
    >
      {/* 回答者 */}
      {points.map((point) => (
        <circle
          key={point.id}
          cx={xScale(point.x)}
          cy={yScale(point.y)}
          r={3}
          fill={colorScale(point.cluster)}
          opacity={0.35}
        />
      ))}

      {/* クラスタ中心 */}
      {clusters.map((cluster) => {
        const centerX = xScale(cluster.center.x);
        const centerY = yScale(cluster.center.y);
        const labelKey = `cluster-${cluster.id}`;

        return (
          <g key={labelKey}>
            <rect
              x={centerX - 9}
              y={centerY - 9}
              width={18}
              height={18}
              fill={colorScale(cluster.id)}
              stroke="white"
              strokeWidth={3}
              transform={`rotate(45 ${centerX} ${centerY})`}
              onClick={() => toggleLabel(labelKey)}
              style={{ cursor: "pointer" }}
            />

            <text
              x={centerX}
              y={centerY}
              textAnchor="middle"
              dominantBaseline="central"
              fill="white"
              fontSize={11}
              fontWeight="bold"
              stroke="rgba(15, 15, 15, 0.75)"
              strokeWidth={3}
              paintOrder="stroke"
              pointerEvents="none"
            >
              {cluster.id}
            </text>

            {visibleLabels.has(labelKey) && (
              <text
                x={centerX + adjustment[cluster.id].x}
                y={centerY + adjustment[cluster.id].y}
                fill="white"
                fontSize={13}
                fontWeight="bold"
                stroke="rgba(15, 15, 15, 0.8)"
                strokeWidth={5}
                paintOrder="stroke"
              >
                {cluster.name}
              </text>
            )}
          </g>
        );
      })}

      {/* Base → Pattern の線 */}
      {basePosition &&
        Object.entries(patternPositions).map(
          ([patternName, position]) => {
            if (!position) {
              return null;
            }

            return (
              <line
                key={`line-${patternName}`}
                x1={xScale(basePosition.x)}
                y1={yScale(basePosition.y)}
                x2={xScale(position.x)}
                y2={yScale(position.y)}
                stroke={patternColors[patternName]}
                strokeWidth={3}
                opacity={0.8}
              />
            );
          }
        )}

      {/* Base */}
      {basePosition && (
        <g>
          <circle
            cx={xScale(basePosition.x)}
            cy={yScale(basePosition.y)}
            r={8}
            fill="white"
            stroke="black"
            strokeWidth={3}
            onClick={() => toggleLabel("base")}
            style={{ cursor: "pointer" }}
          />

          {visibleLabels.has("base") && (
            <text
              x={xScale(basePosition.x) + 14}
              y={yScale(basePosition.y) + 5}
              fill="white"
              fontSize={15}
              fontWeight="bold"
              stroke="rgba(15, 15, 15, 0.9)"
              strokeWidth={5}
              paintOrder="stroke"
            >
              Base
            </text>
          )}
        </g>
      )}

      {/* Pattern A / B / C */}
      {Object.entries(patternPositions).map(
        ([patternName, position]) => {
          if (!position) {
            return null;
          }

          const positionX = xScale(position.x);
          const positionY = yScale(position.y);
          const labelKey = `pattern-${patternName}`;

          return (
            <g key={labelKey}>
              <circle
                cx={positionX}
                cy={positionY}
                r={8}
                fill={patternColors[patternName]}
                stroke="white"
                strokeWidth={2.5}
                onClick={() => toggleLabel(labelKey)}
                style={{ cursor: "pointer" }}
              />

              <text
                x={positionX}
                y={positionY}
                textAnchor="middle"
                dominantBaseline="central"
                fill="white"
                fontSize={10}
                fontWeight="bold"
                stroke="rgba(15, 15, 15, 0.75)"
                strokeWidth={3}
                paintOrder="stroke"
                pointerEvents="none"
              >
                {patternName}
              </text>

              {visibleLabels.has(labelKey) && (
                <text
                  x={positionX + 14}
                  y={positionY + 5}
                  fill="white"
                  fontSize={14}
                  fontWeight="bold"
                  stroke="rgba(15, 15, 15, 0.9)"
                  strokeWidth={5}
                  paintOrder="stroke"
                >
                  Pattern {patternName}
                </text>
              )}
            </g>
          );
        }
      )}
    </svg>
  );
}


// 重み付き131次元空間で最も近いクラスタを探す
export function findNearestCluster(
  weightedVector,
  clusterCenters
) {
  let nearestCluster = null;
  let nearestDistance = Infinity;

  clusterCenters.forEach((center) => {
    const squaredDistance = weightedVector.reduce(
      (sum, value, index) => {
        const difference =
          value - center.vector[index];

        return sum + difference * difference;
      },
      0
    );

    const distance = Math.sqrt(squaredDistance);

    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestCluster = center.cluster;
    }
  });

  return {
    cluster: nearestCluster,
    distance: nearestDistance,
  };
}
