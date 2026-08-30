import UmapMap from "./UmapMap";

const patternColors = {
  A: "#ffdd57",
  B: "#48c78e",
  C: "#f14668",
};

export default function UmapMapSection({
  mapData,
  basePosition,
  patternPositions,
  neighborhoods,
}) {
  return (
    <div className="box">
      <h2 className="subtitle">技術スタックマップ</h2>

      {mapData ? (
        <div>
          <UmapMap
            points={mapData.points}
            basePosition={basePosition}
            patternPositions={patternPositions}
            neighborhoods={neighborhoods}
          />

          <div className="content mb-4">
            <p>
              回答者の技術スタックをUMAPで2次元に圧縮しています。Baseと各Patternの
              位置は、PythonバックエンドのUMAP transformで計算しています。
            </p>

            <div className="mt-4">
              <LegendRow
                graphic={<circle cx="35" cy="12" r="4" fill="#64748b" opacity="0.7" />}
                label="回答者"
                description="それぞれの点が1人の回答者を表します"
              />

              <LegendRow
                graphic={
                  <circle cx="35" cy="12" r="7" fill="white" stroke="black" strokeWidth="3" />
                }
                label="Base"
                description="基準として選択した技術スタックです"
              />

              <LegendRow
                graphic={
                  <>
                    <circle cx="12" cy="12" r="7" fill={patternColors.A} stroke="white" strokeWidth="2" />
                    <circle cx="35" cy="12" r="7" fill={patternColors.B} stroke="white" strokeWidth="2" />
                    <circle cx="58" cy="12" r="7" fill={patternColors.C} stroke="white" strokeWidth="2" />
                  </>
                }
                label="Pattern A / B / C"
                description="Baseに技術を追加した場合の位置です"
              />

              <LegendRow
                graphic={
                  <circle
                    cx="35"
                    cy="12"
                    r="10"
                    fill="#38bdf8"
                    fillOpacity="0.12"
                    stroke="#38bdf8"
                    strokeWidth="2"
                    strokeDasharray="4 3"
                  />
                }
                label="近傍500人の範囲"
                description="2次元マップ上で近い500人が入る円です"
              />

              <LegendRow
                graphic={
                  <line x1="8" y1="12" x2="62" y2="12" stroke={patternColors.A} strokeWidth="3" />
                }
                label="BaseとPatternの変化"
                description="技術を追加したときの位置の変化です"
              />
            </div>

            <p className="is-size-7 has-text-grey mt-4">
              ※ 近傍500人は、UMAPで表示された2次元座標上の距離を使って選んでいます。
            </p>
          </div>
        </div>
      ) : (
        <p>マップデータを読み込んでいます...</p>
      )}
    </div>
  );
}

function LegendRow({ graphic, label, description }) {
  return (
    <div className="is-flex is-align-items-center mb-3">
      <svg width="70" height="24" viewBox="0 0 70 24" className="mr-3">
        {graphic}
      </svg>
      <span>
        {label}
        <span className="has-text-grey ml-2">{description}</span>
      </span>
    </div>
  );
}
