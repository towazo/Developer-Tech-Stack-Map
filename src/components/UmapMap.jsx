import { useState } from "react";
import * as d3 from "d3";
import { clusterColors, clusterLabels } from "../config/clusters";

export default function UmapMap({
  points,
  clusters,
  basePosition,
  patternPositions,
  neighborhoods,
}) {
  const width = 900;
  const height = 600;
  const [visibleLabels, setVisibleLabels] = useState(new Set());

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

  const neighborhoodEntries = [
    ["base", neighborhoods?.base],
    ["A", neighborhoods?.A],
    ["B", neighborhoods?.B],
    ["C", neighborhoods?.C],
  ].filter(([, neighborhood]) => neighborhood);

  const getNeighborhoodCenter = (name) => {
    if (name === "base") {
      return basePosition;
    }

    return patternPositions[name];
  };

  const drawablePositions = [
    ...points.map((point) => ({
      x: point.x,
      y: point.y,
    })),
    ...clusters.map((cluster) => cluster.center),
    ...(basePosition ? [basePosition] : []),
    ...Object.values(patternPositions).filter(Boolean),
  ];

  const addPadding = (extent) => {
    const [minValue, maxValue] = extent;
    const span = maxValue - minValue || 1;
    const padding = span * 0.05;

    return [
      minValue - padding,
      maxValue + padding,
    ];
  };

  const rawXExtent = addPadding(
    d3.extent(drawablePositions, (point) => point.x)
  );

  const rawYExtent = addPadding(
    d3.extent(drawablePositions, (point) => point.y)
  );

  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const xCenter = (rawXExtent[0] + rawXExtent[1]) / 2;
  const yCenter = (rawYExtent[0] + rawYExtent[1]) / 2;
  const xSpan = rawXExtent[1] - rawXExtent[0] || 1;
  const ySpan = rawYExtent[1] - rawYExtent[0] || 1;
  const unitsPerPixel = Math.max(
    xSpan / plotWidth,
    ySpan / plotHeight
  );
  const xExtent = [
    xCenter - (unitsPerPixel * plotWidth) / 2,
    xCenter + (unitsPerPixel * plotWidth) / 2,
  ];
  const yExtent = [
    yCenter - (unitsPerPixel * plotHeight) / 2,
    yCenter + (unitsPerPixel * plotHeight) / 2,
  ];

  const xScale = d3
    .scaleLinear()
    .domain([xExtent[0], xExtent[1]])
    .range([margin.left, width - margin.right]);

  const yScale = d3
    .scaleLinear()
    .domain([yExtent[0], yExtent[1]])
    .range([height - margin.bottom, margin.top]);

  const patternColors = {
    A: "#ffdd57",
    B: "#48c78e",
    C: "#f14668",
  };

  const neighborhoodColors = {
    base: "#38bdf8",
    A: patternColors.A,
    B: patternColors.B,
    C: patternColors.C,
  };

  const getRadiusPixels = (radius) => (
    radius / unitsPerPixel
  );

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{
        width: "100%",
        height: "auto",
      }}
    >
      {points.map((point) => (
        <circle
          key={point.id}
          cx={xScale(point.x)}
          cy={yScale(point.y)}
          r={3}
          fill={clusterColors[point.cluster]}
          opacity={0.36}
        />
      ))}

      {clusters.map((cluster) => {
        const centerX = xScale(cluster.center.x);
        const centerY = yScale(cluster.center.y);

        return (
          <g key={`cluster-${cluster.id}`}>
            <rect
              x={centerX - 6}
              y={centerY - 6}
              width={12}
              height={12}
              fill={clusterColors[cluster.id]}
              stroke="white"
              strokeWidth={2}
              transform={`rotate(45 ${centerX} ${centerY})`}
            />
            <text
              x={centerX + 12}
              y={centerY + 4}
              fill="white"
              fontSize={12}
              fontWeight="bold"
              stroke="rgba(15, 15, 15, 0.85)"
              strokeWidth={4}
              paintOrder="stroke"
              pointerEvents="none"
            >
              {clusterLabels[cluster.id]}
            </text>
          </g>
        );
      })}

      {neighborhoodEntries.map(([name, neighborhood]) => {
        const center = getNeighborhoodCenter(name);

        if (!center || !neighborhood.radius) {
          return null;
        }

        return (
          <circle
            key={`neighborhood-radius-${name}`}
            cx={xScale(center.x)}
            cy={yScale(center.y)}
            r={getRadiusPixels(neighborhood.radius)}
            fill={neighborhoodColors[name]}
            fillOpacity={0.08}
            stroke={neighborhoodColors[name]}
            strokeWidth={2.5}
            strokeOpacity={0.95}
            strokeDasharray="8 6"
          />
        );
      })}

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
