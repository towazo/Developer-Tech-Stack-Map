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

// PCA変換
export function transformToPca(weightedVector, pca) {

  // 各値からSurvey全体の平均を引く
  const centeredVector = weightedVector.map((value, index) => {
    return value - pca.mean[index];
  });

  // PC1を計算
  const pc1 = centeredVector.reduce((sum, value, index) => {
    return sum + value * pca.components[0][index];
  }, 0);

  // PC2を計算
  const pc2 = centeredVector.reduce((sum, value, index) => {
    return sum + value * pca.components[1][index];
  }, 0);

  return {
    x: pc1,
    y: pc2,
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