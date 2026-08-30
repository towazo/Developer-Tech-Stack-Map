import { useEffect, useState } from "react";
import { translateMetadataValue } from "../utils/metadataTranslations";

const STACK_LABELS = {
  base: "Base",
  A: "Pattern A",
  B: "Pattern B",
  C: "Pattern C",
};

export default function NeighborhoodDetail({ neighborhoods }) {
  const availableKeys = Object.keys(STACK_LABELS).filter(
    (key) => neighborhoods?.[key]?.statistics
  );
  const [selectedKey, setSelectedKey] = useState("base");

  useEffect(() => {
    if (!availableKeys.includes(selectedKey)) {
      setSelectedKey(availableKeys[0] ?? "base");
    }
  }, [availableKeys, selectedKey]);

  if (availableKeys.length === 0) {
    return (
      <div className="box">
        <h2 className="title is-4">近傍回答者の詳細</h2>
        <p>Baseの技術を選択すると、近傍500人の統計を表示します。</p>
      </div>
    );
  }

  const statistics = neighborhoods[selectedKey].statistics;

  return (
    <div className="box">
      <h2 className="title is-4">近傍回答者の詳細</h2>

      <div className="tabs is-toggle">
        <ul>
          {availableKeys.map((key) => (
            <li key={key} className={selectedKey === key ? "is-active" : ""}>
              <a onClick={() => setSelectedKey(key)}>{STACK_LABELS[key]}</a>
            </li>
          ))}
        </ul>
      </div>

      <h3 className="title is-5">{STACK_LABELS[selectedKey]}の近傍</h3>
      <p>
        UMAPの2次元マップ上で近い回答者：
        <strong>{statistics.count.toLocaleString()}人</strong>
      </p>
      <p>
        全回答者に占める割合：
        <strong>{statistics.rate.toFixed(1)}%</strong>
      </p>

      <hr />

      <div className="columns is-variable is-6 is-centered pb-5">
        <div className="column is-6">
          <h4 className="title is-6">特徴的な利用技術 Top10</h4>

          {statistics.topTechnologies.map((technology) => (
            <div key={technology.rank} className="mb-4">
              <div className="is-flex is-justify-content-space-between">
                <div>
                  <strong>{technology.name}</strong>
                  <span className="tag is-light ml-2">
                    {technology.categoryLabel}
                  </span>
                </div>
                <strong>{technology.usageRate.toFixed(1)}%</strong>
              </div>

              <progress
                className="progress is-info mb-1"
                value={technology.usageRate}
                max="100"
              >
                {technology.usageRate.toFixed(1)}%
              </progress>

              <p className="is-size-7 has-text-grey">
                全体：{technology.overallUsageRate.toFixed(1)}% ／ 全体との差：
                {technology.differencePoint >= 0 ? "+" : ""}
                {technology.differencePoint.toFixed(1)}pt
              </p>
            </div>
          ))}
        </div>

        <div className="column is-6">
          <h4 className="title is-6">回答者の傾向</h4>

          {Object.entries(statistics.metadata).map(([metadataKey, metadata]) => (
            <div key={metadataKey} className="metadata-group">
              <strong>{metadata.label}</strong>

              {metadata.items.map((item) => (
                <div key={`${metadataKey}-${item.value}`} className="mt-1">
                  <p>
                    {item.rank}. {translateMetadataValue(metadataKey, item.value)}
                  </p>
                  <p className="is-size-7 has-text-grey">
                    近傍：{item.usageRate.toFixed(1)}% ／ 全体：
                    {item.overallRate.toFixed(1)}% ／ 差：
                    {item.differencePoint >= 0 ? "+" : ""}
                    {item.differencePoint.toFixed(1)}pt
                  </p>
                </div>
              ))}
            </div>
          ))}

          <h4 className="title is-6 mt-4">実務経験年数</h4>
          <p>
            中央値：
            <strong>{statistics.workExperience.median.toFixed(0)}年</strong>
            <span className="is-size-7 has-text-grey ml-4">
              中央50%の範囲：{statistics.workExperience.q1.toFixed(0)}年 ～
              {statistics.workExperience.q3.toFixed(0)}年
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
