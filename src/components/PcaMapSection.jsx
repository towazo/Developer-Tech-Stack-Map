import PcaMap from "./PcaMap";

export default function PcaMapSection({
  mapData,
  clusterData,
  basePosition,
  patternPositions,
}) {
  const clusterColors = [
    "#4e79a7",
    "#f28e2c",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc949",
  ];

  const patternColors = {
    A: "#ffdd57",
    B: "#48c78e",
    C: "#f14668",
  };

  return (
    <div className="box">
      <h2 className="subtitle">
        技術スタックマップ
      </h2>

      {mapData && clusterData ? (
        <div>
          <PcaMap
            points={mapData.points}
            clusters={clusterData.clusters}
            basePosition={basePosition}
            patternPositions={patternPositions}
          />

          <div className="content mb-4">
            <p>
              使用技術の傾向から回答者を6つのクラスタに分類し、
              その技術スタックをUMAPによって2次元上に表示しています。
              分析対象15,239人のうち、見やすさのため5,000人を表示しています。
            </p>

            {/* 凡例 */}
            <div className="mt-4">

              {/* 回答者 */}
              <div className="is-flex is-align-items-center mb-3">
                <svg
                  width="70"
                  height="24"
                  viewBox="0 0 70 24"
                  className="mr-3"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="4"
                    fill={clusterColors[0]}
                    opacity="0.7"
                  />
                  <circle
                    cx="28"
                    cy="12"
                    r="4"
                    fill={clusterColors[1]}
                    opacity="0.7"
                  />
                  <circle
                    cx="44"
                    cy="12"
                    r="4"
                    fill={clusterColors[4]}
                    opacity="0.7"
                  />
                </svg>

                <span>
                  回答者
                  <span className="has-text-grey ml-2">
                    （色は所属クラスタ）
                  </span>
                </span>
              </div>

              {/* クラスタ中心 */}
              <div className="is-flex is-align-items-center mb-3">
                <svg
                  width="70"
                  height="28"
                  viewBox="0 0 70 28"
                  className="mr-3"
                >
                  <rect
                    x="22"
                    y="7"
                    width="14"
                    height="14"
                    fill={clusterColors[0]}
                    stroke="white"
                    strokeWidth="2"
                    transform="rotate(45 29 14)"
                  />
                </svg>

                <span>
                  クラスタ中心
                  <span className="has-text-grey ml-2">
                    （色は所属クラスタ）
                  </span>
                </span>
              </div>

              {/* Base */}
              <div className="is-flex is-align-items-center mb-3">
                <svg
                  width="70"
                  height="24"
                  viewBox="0 0 70 24"
                  className="mr-3"
                >
                  <circle
                    cx="29"
                    cy="12"
                    r="7"
                    fill="white"
                    stroke="black"
                    strokeWidth="3"
                  />
                </svg>

                <span>
                  Base
                  <span className="has-text-grey ml-2">
                    （選択した技術スタック）
                  </span>
                </span>
              </div>

              {/* Pattern */}
              <div className="is-flex is-align-items-center mb-3">
                <svg
                  width="70"
                  height="24"
                  viewBox="0 0 70 24"
                  className="mr-3"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="7"
                    fill={patternColors.A}
                    stroke="white"
                    strokeWidth="2"
                  />

                  <circle
                    cx="35"
                    cy="12"
                    r="7"
                    fill={patternColors.B}
                    stroke="white"
                    strokeWidth="2"
                  />

                  <circle
                    cx="58"
                    cy="12"
                    r="7"
                    fill={patternColors.C}
                    stroke="white"
                    strokeWidth="2"
                  />
                </svg>

                <span>
                  Pattern A / B / C
                  <span className="has-text-grey ml-2">
                    （Baseに技術を追加した場合の位置）
                  </span>
                </span>
              </div>

              {/* Base → Pattern */}
              <div className="is-flex is-align-items-center mb-3">
                <svg
                  width="70"
                  height="24"
                  viewBox="0 0 70 24"
                  className="mr-3"
                >
                  <line
                    x1="8"
                    y1="12"
                    x2="62"
                    y2="12"
                    stroke={patternColors.A}
                    strokeWidth="3"
                  />
                </svg>

                <span>
                  Base → Pattern
                  <span className="has-text-grey ml-2">
                    （技術を追加した際の位置の変化）
                  </span>
                </span>
              </div>
            </div>

            <p className="is-size-7 has-text-grey mt-4">
              ※ クラスタ中心・Base・Patternはクリックすると名前を表示し、
              もう一度クリックすると非表示になります。
            </p>

            <p className="is-size-7 has-text-grey">
              ※ マップは131次元の技術スタックデータをUMAPで2次元に圧縮したものです。
              最も近いクラスタの判定は、マップ上の距離ではなく、
              元の重み付き131次元データで行っています。
              Base・Patternの表示位置は、PythonバックエンドのUMAP transformで計算しています。
            </p>
          </div>
        </div>
      ) : (
        <p>データを読み込んでいます...</p>
      )}
    </div>
  );
}
