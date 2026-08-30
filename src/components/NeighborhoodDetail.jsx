import { useEffect, useState } from "react";
import RespondentTrendPieChart from "./RespondentTrendPieChart";

const STACK_LABELS = {
  base: "現在の技術",
  A: "学習プラン A",
  B: "学習プラン B",
  C: "学習プラン C",
};

export default function NeighborhoodDetail({ neighborhoods, onBack }) {
  const availableKeys = Object.keys(STACK_LABELS).filter(
    (key) => neighborhoods?.[key]?.statistics
  );
  const [selectedKey, setSelectedKey] = useState("base");
  const [selectedTechnologyCategory, setSelectedTechnologyCategory] = useState("language");
  const [selectedTrendKey, setSelectedTrendKey] = useState("devType");

  useEffect(() => {
    if (!availableKeys.includes(selectedKey)) {
      setSelectedKey(availableKeys[0] ?? "base");
    }
  }, [availableKeys, selectedKey]);

  if (availableKeys.length === 0) {
    return (
      <div className="box neighborhood-detail">
        <h2 className="title is-4">似ているエンジニアの傾向</h2>
        <p>現在使っている技術を選択すると、技術構成が似ている500人の傾向を表示します。</p>
        <BackButton onBack={onBack} />
      </div>
    );
  }

  const statistics = neighborhoods[selectedKey].statistics;
  const selectedCategory = statistics.topTechnologiesByCategory.find(
    (category) => category.key === selectedTechnologyCategory
  ) ?? statistics.topTechnologiesByCategory[0];

  return (
    <div className="box neighborhood-detail">
      <h2 className="title is-4">似ているエンジニアの傾向</h2>

      <div className="tabs is-toggle">
        <ul>
          {availableKeys.map((key) => (
            <li key={key} className={selectedKey === key ? "is-active" : ""}>
              <a onClick={() => setSelectedKey(key)}>{STACK_LABELS[key]}</a>
            </li>
          ))}
        </ul>
      </div>

      <div className="columns is-variable is-6 is-centered pb-2">
        <div className="column is-6">
          <h4 className="title is-6">人気の技術 Top3</h4>

          <div className="field mb-4">
            <label className="label" htmlFor="technology-category-select">
              表示するジャンル
            </label>
            <div className="control">
              <div className="select is-fullwidth">
                <select
                  id="technology-category-select"
                  value={selectedCategory.key}
                  onChange={(event) => setSelectedTechnologyCategory(event.target.value)}
                >
                  {statistics.topTechnologiesByCategory.map((category) => (
                    <option key={category.key} value={category.key}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {selectedCategory.technologies.map((technology) => (
            <div key={technology.name} className="mb-4">
              <div className="is-flex is-justify-content-space-between">
                <strong>{technology.rank}. {technology.name}</strong>
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

          <div className="mt-5 pt-4 respondent-work-experience">
            <h4 className="title is-6 mb-3">実務経験年数</h4>
            <p>
              中央値：
              <strong>{statistics.workExperience.median.toFixed(0)}年</strong>
            </p>
            <p className="is-size-7 has-text-grey mt-1">
              中央50%の範囲：{statistics.workExperience.q1.toFixed(0)}年 ～
              {statistics.workExperience.q3.toFixed(0)}年
            </p>
          </div>
        </div>

        <div className="column is-6">
          <h4 className="title is-6">回答者の傾向</h4>

          <div className="field mb-4">
            <label className="label" htmlFor="respondent-trend-select">
              表示する項目
            </label>
            <div className="control">
              <div className="select is-fullwidth">
                <select
                  id="respondent-trend-select"
                  value={selectedTrendKey}
                  onChange={(event) => setSelectedTrendKey(event.target.value)}
                >
                  {Object.entries(statistics.metadata).map(([metadataKey, metadata]) => (
                    <option key={metadataKey} value={metadataKey}>
                      {metadata.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <RespondentTrendPieChart
            metadataKey={selectedTrendKey}
            items={statistics.metadata[selectedTrendKey].items}
          />
          <BackButton onBack={onBack} />
        </div>
      </div>
    </div>
  );
}

function BackButton({ onBack }) {
  return (
    <div className="neighborhood-detail-back">
      <button type="button" className="button" onClick={onBack}>
        技術スタックマップへ戻る
      </button>
    </div>
  );
}
