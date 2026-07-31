export default function StackResult({
  nearestClusters,
  clusterData,
}) {
  const getClusterName = (clusterId) => {
    const cluster = clusterData?.clusters.find(
      (cluster) => cluster.id === clusterId
    );

    return cluster ? cluster.name : "未判定";
  };

  return (
    <div className="box">
      <h2 className="title is-4">
        技術スタックの傾向
      </h2>

      {nearestClusters.base ? (
        <div>
          <p className="mb-3">
            <span className="tag is-info mr-2">
              Base
            </span>

            最も近い傾向：
            <strong>
              {getClusterName(
                nearestClusters.base.cluster
              )}
            </strong>
          </p>

          {["A", "B", "C"].map((patternName) => {
            const result =
              nearestClusters[patternName];

            if (!result) {
              return null;
            }

            const tagClass =
              patternName === "A"
                ? "is-warning"
                : patternName === "B"
                ? "is-success"
                : "is-danger";

            return (
              <p
                key={patternName}
                className="mb-3"
              >
                <span
                  className={`tag ${tagClass} mr-2`}
                >
                  Pattern {patternName}
                </span>

                最も近い傾向：
                <strong>
                  {getClusterName(
                    result.cluster
                  )}
                </strong>
              </p>
            );
          })}
        </div>
      ) : (
        <p>
          Base技術を選択すると判定結果が表示されます。
        </p>
      )}
    </div>
  );
}
