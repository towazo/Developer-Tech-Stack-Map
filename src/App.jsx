import { useEffect, useState } from "react";
import TechnologyPanel from "./components/TechnologyPanel";
import UmapMapSection from "./components/UmapMapSection";
import NeighborhoodDetail from "./components/NeighborhoodDetail";
import Footer from "./components/Footer";
import { analyzeTechnologyStack } from "./utils/browserAnalysis";

export default function App() {
  const [mapData, setMapData] = useState(null);
  const [technologyData, setTechnologyData] = useState(null);
  const [selectedBase, setSelectedBase] = useState([]);
  const [activeTab, setActiveTab] = useState("base");
  const [selectedPatterns, setSelectedPatterns] = useState({
    A: [],
    B: [],
    C: [],
  });
  const [basePosition, setBasePosition] = useState(null);
  const [patternPositions, setPatternPositions] = useState({
    A: null,
    B: null,
    C: null,
  });
  const [neighborhoods, setNeighborhoods] = useState({
    base: null,
    A: null,
    B: null,
    C: null,
  });
  const [analysisError, setAnalysisError] = useState(null);

  //useEffect→あるタイミングで処理を実行するモノ
  useEffect(() => {
    fetch("/data/map_points.json")
      .then((response) => response.json())
      .then((data) => {
        setMapData(data);
      });

    fetch("/data/technologies.json")
      .then((response) => response.json())
      .then((data) => {
        setTechnologyData(data);
        console.log("technologies.json:", data);
      });

  }, []);

  useEffect(() => {
    let isCancelled = false;

    // 必要なデータがまだ読み込まれていなければ何もしない
    if (!technologyData) {
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

      setNeighborhoods({
        base: null,
        A: null,
        B: null,
        C: null,
      });
      setAnalysisError(null);


      return () => {
        isCancelled = true;
      };
    }

    // 131技術それぞれの重み
    // 技術一覧から
    // ① UMAP上の表示位置
    // の両方を計算する
    const calculateStack = async (selectedIndexes) => {
      try {
        const position = await analyzeTechnologyStack(
          selectedIndexes,
          technologyData
        );
        return { position, neighborhood: position.neighborhood };
      } catch (error) {
        console.error("ブラウザ内の分析処理に失敗しました。", error);
        setAnalysisError(
          "分析データを読み込めませんでした。ページを再読み込みしてください。"
        );
        return { position: null, neighborhood: null };
      }
    };

    const updateStackResults = async () => {
      setAnalysisError(null);
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

      setNeighborhoods({
        base: baseResult.neighborhood,
        A: patternResults.A?.neighborhood ?? null,
        B: patternResults.B?.neighborhood ?? null,
        C: patternResults.C?.neighborhood ?? null,
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

        {analysisError && (
          <div className="notification is-danger is-light" role="alert">
            {analysisError}
          </div>
        )}

        <UmapMapSection
          mapData={mapData}
          basePosition={basePosition}
          patternPositions={patternPositions}
          neighborhoods={neighborhoods}
        />

        <NeighborhoodDetail neighborhoods={neighborhoods} />

        <Footer />
      </div>
    </section>
  );
}
