import { arc, pie } from "d3";
import { translateMetadataValue } from "../utils/metadataTranslations";

const COLORS = ["#4e79a7", "#f28e2c", "#59a14f", "#e15759", "#b07aa1", "#76b7b2"];

function buildChartItems(metadataKey, items) {
  const visibleItems = items.filter(
    (item) => item.value !== "Other:" && item.usageRate > 0
  );
  const visibleTotal = visibleItems.reduce(
    (total, item) => total + item.usageRate,
    0
  );
  const normalizedItems = visibleItems.map((item) => ({
    ...item,
    chartRate: visibleTotal ? item.usageRate / visibleTotal * 100 : 0,
  }));
  const leadingItems = normalizedItems.slice(0, 5).map((item) => ({
    label: translateMetadataValue(metadataKey, item.value),
    value: item.chartRate,
  }));
  const otherRate = normalizedItems
    .slice(5)
    .reduce((total, item) => total + item.chartRate, 0);

  return otherRate > 0.05
    ? [...leadingItems, { label: "上位5項目以外", value: otherRate }]
    : leadingItems;
}

export default function RespondentTrendPieChart({ metadataKey, items }) {
  const chartItems = buildChartItems(metadataKey, items);
  const slices = pie()
    .sort(null)
    .value((item) => item.value)(chartItems);
  const createArc = arc().innerRadius(0).outerRadius(92);

  return (
    <div className="respondent-trend-chart">
      <svg
        className="respondent-trend-pie"
        viewBox="0 0 200 200"
        role="img"
        aria-label="似ているエンジニアの構成比を示す円グラフ"
      >
        <g transform="translate(100, 100)">
          {slices.map((slice, index) => (
            <path
              key={slice.data.label}
              d={createArc(slice)}
              fill={COLORS[index]}
              stroke="#111827"
              strokeWidth="2"
            >
              <title>{`${slice.data.label}: ${slice.data.value.toFixed(1)}%`}</title>
            </path>
          ))}
        </g>
      </svg>

      <ul className="respondent-trend-legend">
        {chartItems.map((item, index) => (
          <li key={item.label}>
            <span
              className="respondent-trend-swatch"
              style={{ backgroundColor: COLORS[index] }}
              aria-hidden="true"
            />
            <span className="respondent-trend-label">{item.label}</span>
            <strong>{item.value.toFixed(1)}%</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
