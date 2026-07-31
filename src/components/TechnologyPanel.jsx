import TechnologySelector from "./TechnologySelector";

export default function TechnologyPanel({
  technologyData,
  activeTab,
  setActiveTab,
  selectedBase,
  selectedPatterns,
  onToggle,
}) {
  return (
    <div className="box">
      <h2 className="title is-4">
        {activeTab === "base"
          ? "Base技術を選択"
          : `Pattern ${activeTab} の追加技術を選択`}
      </h2>

      <div className="tabs is-toggle is-toggle-rounded">
        <ul>
          <li className={activeTab === "base" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("base")}>
              Base
            </a>
          </li>

          <li className={activeTab === "A" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("A")}>
              Pattern A
            </a>
          </li>

          <li className={activeTab === "B" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("B")}>
              Pattern B
            </a>
          </li>

          <li className={activeTab === "C" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("C")}>
              Pattern C
            </a>
          </li>
        </ul>
      </div>

      {technologyData ? (
        <TechnologySelector
          categories={technologyData.categories}
          mode={activeTab}
          baseSelected={selectedBase}
          patternSelected={
            activeTab === "base"
              ? []
              : selectedPatterns[activeTab]
          }
          onToggle={onToggle}
        />
      ) : (
        <p>技術データを読み込んでいます...</p>
      )}
    </div>
  );
}
