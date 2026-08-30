import { useEffect, useState } from "react";
import TechnologyPanel from "./components/TechnologyPanel";
import StackResult from "./components/StackResult";
import PcaMapSection from "./components/PcaMapSection";
import ClusterDetail from "./components/ClusterDetail";
import Footer from "./components/Footer";
import {
  createBinaryVector,
  createWeightVector,
  applyWeights,
  findNearestAnchorPosition,
  findNearestCluster,
} from "./utils/techVector";

export default function App() {
  const [mapData, setMapData] = useState(null);
  const [clusterData, setClusterData] = useState(null);
  const [technologyData, setTechnologyData] = useState(null);
  const [selectedBase, setSelectedBase] = useState([]);
  const [activeTab, setActiveTab] = useState("base");
  const [selectedPatterns, setSelectedPatterns] = useState({
    A: [],
    B: [],
    C: [],
  });
  const [modelData, setModelData] = useState(null);
  const [basePosition, setBasePosition] = useState(null);
  const [patternPositions, setPatternPositions] = useState({
    A: null,
    B: null,
    C: null,
  });
  const [nearestClusters, setNearestClusters] = useState({
    base: null,
    A: null,
    B: null,
    C: null,
  });

  //useEffect→あるタイミングで処理を実行するモノ
  useEffect(() => {
    fetch("/data/map_points.json")
      .then((response) => response.json())
      .then((data) => {
        setMapData(data);
      });

    fetch("/data/clusters.json")
      .then((response) => response.json())
      .then((data) => {
        setClusterData(data);
      });

    fetch("/data/technologies.json")
      .then((response) => response.json())
      .then((data) => {
        setTechnologyData(data);
        console.log("technologies.json:", data);
      });

    fetch("/data/model.json")
      .then((response) => response.json())
      .then((data) => {
        setModelData(data);
        console.log("model.json:", data);
      });
  }, []);

  useEffect(() => {
    let isCancelled = false;

    // 必要なデータがまだ読み込まれていなければ何もしない
    if (!technologyData || !modelData) {
      return () => {
        isCancelled = true;
      };
    }

    // Baseが空ならすべての結果を消す
    if (selectedBase.length === 0) {
      setBasePosition(null);

      setPatternPositions({
        A: null,
        B: null,
        C: null,
      });

      setNearestClusters({
        base: null,
        A: null,
        B: null,
        C: null,
      });

      return () => {
        isCancelled = true;
      };
    }

    // 131技術それぞれの重み
    const weightVector = createWeightVector(
      technologyData.categories,
      modelData.featureCount
    );

    // 技術一覧から
    // ① UMAP上の表示位置
    // ② 最も近いクラスタ
    // の両方を計算する
    const fetchUmapPosition = async (
      selectedIndexes,
      fallbackPosition
    ) => {
      try {
        const response = await fetch("/api/umap-position", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            selectedIndexes,
          }),
        });

        if (!response.ok) {
          throw new Error(
            `UMAP API returned ${response.status}`
          );
        }

        const data = await response.json();

        if (!data.ok) {
          throw new Error(data.error || "UMAP API failed");
        }

        return {
          x: data.x,
          y: data.y,
          method: data.method,
        };
      } catch (error) {
        console.warn(
          "UMAP APIが利用できないため、近傍アンカー座標を使用します。",
          error
        );

        return fallbackPosition;
      }
    };

    const calculateStack = async (selectedIndexes) => {
      const binaryVector = createBinaryVector(
        selectedIndexes,
        modelData.featureCount
      );

      const weightedVector = applyWeights(
        binaryVector,
        weightVector
      );

      const fallbackPosition = findNearestAnchorPosition(
        weightedVector,
        weightVector,
        modelData.respondentAnchors
      );

      const nearestCluster = findNearestCluster(
        weightedVector,
        modelData.clusterCentersWeighted
      );

      const position = await fetchUmapPosition(
        selectedIndexes,
        fallbackPosition
      );

      return {
        position,
        nearestCluster,
      };
    };

    const updateStackResults = async () => {
      // -------------------------
      // Base
      // -------------------------

      const baseResult = await calculateStack(selectedBase);

      // -------------------------
      // Pattern A・B・C
      // -------------------------

      const patternResults = {
        A:
          selectedPatterns.A.length > 0
            ? await calculateStack([
                ...selectedBase,
                ...selectedPatterns.A,
              ])
            : null,

        B:
          selectedPatterns.B.length > 0
            ? await calculateStack([
                ...selectedBase,
                ...selectedPatterns.B,
              ])
            : null,

        C:
          selectedPatterns.C.length > 0
            ? await calculateStack([
                ...selectedBase,
                ...selectedPatterns.C,
              ])
            : null,
      };

      if (isCancelled) {
        return;
      }

      setBasePosition(baseResult.position);

      setPatternPositions({
        A: patternResults.A?.position ?? null,
        B: patternResults.B?.position ?? null,
        C: patternResults.C?.position ?? null,
      });

      setNearestClusters({
        base: baseResult.nearestCluster,
        A: patternResults.A?.nearestCluster ?? null,
        B: patternResults.B?.nearestCluster ?? null,
        C: patternResults.C?.nearestCluster ?? null,
      });

      console.log(
        "Baseの最近傍クラスタ:",
        baseResult.nearestCluster
      );

      console.log("Patternの最近傍クラスタ:", {
        A: patternResults.A?.nearestCluster ?? null,
        B: patternResults.B?.nearestCluster ?? null,
        C: patternResults.C?.nearestCluster ?? null,
      });
    };

    updateStackResults();

    return () => {
      isCancelled = true;
    };
  }, [
    selectedBase,
    selectedPatterns,
    technologyData,
    modelData,
  ]);

  // 技術の選択状態を切り替える関数
  //Base
  const toggleTechnology = (index) => {
    // Baseタブの場合
    if (activeTab === "base") {
      // すでに選択されている場合は解除
      if (selectedBase.includes(index)) {
        setSelectedBase(
          selectedBase.filter((i) => i !== index)
        );
      }
      // 選択されていなければ追加
      else {
        setSelectedBase([
          ...selectedBase,
          index
        ]);

        // Baseになった技術はA・B・Cの追加技術から取り除く
        setSelectedPatterns({
          A: selectedPatterns.A.filter((i) => i !== index),
          B: selectedPatterns.B.filter((i) => i !== index),
          C: selectedPatterns.C.filter((i) => i !== index),
        });
      }

      return;
    }

    // Pattern A・B・C
    // Baseで選択されている技術の場合は何もしない
    if (selectedBase.includes(index)) {
      return;
    }

    // 現在のPatternの選択状態を取得
    const currentPattern = selectedPatterns[activeTab];

    // すでにPatternで選択されていれば解除
    if (currentPattern.includes(index)) {
      setSelectedPatterns({
        ...selectedPatterns,
        [activeTab]: currentPattern.filter(
          (i) => i !== index
        ),
      });
    }
    // 未選択なら追加
    else {
      setSelectedPatterns({
        ...selectedPatterns,
        [activeTab]: [
          ...currentPattern,
          index
        ],
      });
    }
  };

    return (
    <section className="section">
      <div className="container">
        <h1 className="title">
          Developer Tech Stack Map
        </h1>

        <TechnologyPanel
          technologyData={technologyData}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedBase={selectedBase}
          selectedPatterns={selectedPatterns}
          onToggle={toggleTechnology}
        />

        <StackResult
          nearestClusters={nearestClusters}
          clusterData={clusterData}
        />

        <PcaMapSection
          mapData={mapData}
          clusterData={clusterData}
          basePosition={basePosition}
          patternPositions={patternPositions}
        />

        <ClusterDetail
          clusterData={clusterData}
        />

        <Footer />
      </div>
    </section>
  );
}
