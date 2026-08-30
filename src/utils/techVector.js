//0 or 1の131個の配列にしてる
export function createBinaryVector(selectedIndexes, featureCount) {
  const vector = Array(featureCount).fill(0);

  selectedIndexes.forEach((index)=>{
    vector[index]=1;
  });
  return vector;
}

//配列に対応した重みの配列を作成
export function createWeightVector(categories, featureCount) {
  const weights = Array(featureCount).fill(0);

  categories.forEach((category) => {
    category.technologies.forEach((technology) => {
      weights[technology.index] = technology.weight;
    });
  });

  return weights;
}

export function applyWeights(binaryVector, weightVector) {
  return binaryVector.map((value, index) => {
    return value*weightVector[index];
  });
}

// UMAPはブラウザで簡単に同じtransformを再現できない。
// そのため、重み付き131次元空間で最も近い既存回答者を探し、
// その回答者のUMAP座標をBase/Patternの表示位置として使う。
export function findNearestAnchorPosition(
  weightedVector,
  weightVector,
  respondentAnchors
) {
  if (!respondentAnchors || respondentAnchors.length === 0) {
    return null;
  }

  const selectedSquaredNorm = weightedVector.reduce(
    (sum, value) => {
      return sum + value * value;
    },
    0
  );

  let nearestAnchor = null;
  let nearestSquaredDistance = Infinity;

  respondentAnchors.forEach((anchor) => {
    const anchorFeatures = Array.isArray(anchor)
      ? anchor[5]
      : anchor.features;

    const anchorSquaredNorm = Array.isArray(anchor)
      ? anchor[4]
      : anchor.squaredNorm;

    const dotProduct = anchorFeatures.reduce(
      (sum, featureIndex) => {
        return sum + weightedVector[featureIndex] * weightVector[featureIndex];
      },
      0
    );

    const squaredDistance =
      selectedSquaredNorm + anchorSquaredNorm - 2 * dotProduct;

    if (squaredDistance < nearestSquaredDistance) {
      nearestSquaredDistance = squaredDistance;
      nearestAnchor = anchor;
    }
  });

  if (!nearestAnchor) {
    return null;
  }

  return {
    x: Array.isArray(nearestAnchor)
      ? nearestAnchor[2]
      : nearestAnchor.x,
    y: Array.isArray(nearestAnchor)
      ? nearestAnchor[3]
      : nearestAnchor.y,
    anchorId: Array.isArray(nearestAnchor)
      ? nearestAnchor[0]
      : nearestAnchor.id,
    anchorCluster: Array.isArray(nearestAnchor)
      ? nearestAnchor[1]
      : nearestAnchor.cluster,
    anchorDistance: Math.sqrt(
      Math.max(nearestSquaredDistance, 0)
    ),
  };
}

// 重み付き131次元空間で最も近いクラスタを探す
export function findNearestCluster(
  weightedVector,
  clusterCenters
) {
  // 現時点で一番近いクラスタ
  let nearestCluster = null;

  // 現時点で一番短い距離
  // 最初はどんな距離よりも大きいInfinityにする
  let nearestDistance = Infinity;

  // 6個のクラスタ中心を順番に調べる
  clusterCenters.forEach((center) => {

    // ユーザーとクラスタ中心の距離を計算
    const squaredDistance = weightedVector.reduce(
      (sum, value, index) => {

        // 同じindex同士の差
        const difference =
          value - center.vector[index];

        // 差を2乗して合計する
        return sum + difference * difference;
      },
      0
    );

    // 最後に平方根を取る
    const distance = Math.sqrt(squaredDistance);

    // 今までで一番近ければ更新
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
