import { useState } from "react";
import { translateMetadataValue } from "../utils/metadataTranslations";

export default function ClusterDetail({
  clusterData,
}) {
  // 現在表示しているクラスタのID
  const [selectedClusterId, setSelectedClusterId] = useState(0);

  // データ読み込み前
  if (!clusterData) {
    return (
      <div className="box">
        <h2 className="title is-4">
          クラスタ詳細
        </h2>

        <p>
          クラスタデータを読み込んでいます...
        </p>
      </div>
    );
  }

  // 選択中のクラスタを取得
  const cluster = clusterData.clusters.find(
    (cluster) => cluster.id === selectedClusterId
  );

  return (
    <div className="box">
      <h2 className="title is-4">
        クラスタ詳細
      </h2>

      {/* クラスタ切り替え */}
      <div className="tabs is-toggle">
        <ul>
          {clusterData.clusters.map((clusterItem) => (
            <li
              key={clusterItem.id}
              className={
                selectedClusterId === clusterItem.id
                  ? "is-active"
                  : ""
              }
            >
              <a
                onClick={() =>
                  setSelectedClusterId(clusterItem.id)
                }
              >
                {clusterItem.name}
              </a>
            </li>
          ))}
        </ul>
      </div>

      {cluster && (
        <div>
          {/* クラスタ基本情報 */}
          <h3 className="title is-5">
            {cluster.name}
          </h3>

          <p>
            回答者数：
            <strong>
              {cluster.count.toLocaleString()}人
            </strong>
          </p>

          <p>
            全体の割合：
            <strong>
              {cluster.rate.toFixed(1)}%
            </strong>
          </p>

          <hr />

          {/* 左右の内容を中央寄せ */}
          <div className="columns is-variable is-6 is-centered pb-5">

            {/* 左側：特徴的な技術 */}
            <div className="column is-6">
              <h4 className="title is-6">
                特徴的な技術 Top10
              </h4>

              {cluster.topTechnologies.map((technology) => (
                <div
                  key={technology.rank}
                  className="mb-4"
                >
                  <div className="is-flex is-justify-content-space-between">
                    <div>
                      <strong>
                        {technology.name}
                      </strong>

                      <span className="tag is-light ml-2">
                        {technology.categoryLabel}
                      </span>
                    </div>

                    <strong>
                      {technology.clusterUsageRate.toFixed(1)}%
                    </strong>
                  </div>

                  <progress
                    className="progress is-info mb-1"
                    value={technology.clusterUsageRate}
                    max="100"
                  >
                    {technology.clusterUsageRate.toFixed(1)}%
                  </progress>

                  <p className="is-size-7 has-text-grey">
                    全体：
                    {technology.overallUsageRate.toFixed(1)}%
                    ／ 全体との差：
                    {technology.differencePoint >= 0 ? "+" : ""}
                    {technology.differencePoint.toFixed(1)}pt
                  </p>
                </div>
              ))}
            </div>

            {/* 右側：回答者の傾向 */}
            <div className="column is-6">
              <h4 className="title is-6">
                回答者の傾向
              </h4>

              {Object.entries(cluster.metadata).map(([metadataKey, metadataItem]) => (
                <div
                  key={metadataItem.label}
                  className="metadata-group"
                >
                  <strong>
                    {metadataItem.label}
                  </strong>

                  {metadataItem.items.slice(0, 3).map((item) => (
                    <div
                      key={item.rank}
                      className="mt-1"
                    >
                      <p>
                        {item.rank}. {translateMetadataValue(metadataKey, item.value)}
                      </p>

                      <p className="is-size-7 has-text-grey">
                        このクラスタ：
                        {item.clusterRate.toFixed(1)}%
                        ／ 全体：
                        {item.overallRate.toFixed(1)}%
                        ／ 差：
                        {item.differencePoint >= 0 ? "+" : ""}
                        {item.differencePoint.toFixed(1)}pt
                      </p>
                    </div>
                  ))}
                </div>
              ))}

              <h4 className="title is-6 mt-4">
                実務経験
              </h4>

              <p>
                中央値：
                <strong>
                  {cluster.workExperience.median.toFixed(0)}年
                </strong>

                <span className="is-size-7 has-text-grey ml-4">
                  中央50%の範囲：
                  {cluster.workExperience.q1.toFixed(0)}年
                  〜
                  {cluster.workExperience.q3.toFixed(0)}年
                </span>
              </p>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
