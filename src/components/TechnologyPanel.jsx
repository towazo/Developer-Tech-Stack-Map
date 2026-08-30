import TechnologySelector from "./TechnologySelector";
import { useEffect, useMemo, useRef, useState } from "react";

export default function TechnologyPanel({
  technologyData,
  activeTab,
  setActiveTab,
  selectedBase,
  selectedPatterns,
  onToggle,
}) {
  const [selectedCategoryKey, setSelectedCategoryKey] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [highlightedTechnologyIndex, setHighlightedTechnologyIndex] =
    useState(null);
  const searchInputRef = useRef(null);
  const highlightTimeoutRef = useRef(null);

  useEffect(() => {
    return () => {
      if (highlightTimeoutRef.current) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!technologyData || technologyData.categories.length === 0) {
      return;
    }

    const categoryExists = technologyData.categories.some(
      (category) => category.key === selectedCategoryKey
    );

    if (!categoryExists) {
      setSelectedCategoryKey(technologyData.categories[0].key);
    }
  }, [technologyData, selectedCategoryKey]);

  const visibleCategories = technologyData
    ? technologyData.categories.filter(
        (category) => category.key === selectedCategoryKey
      )
    : [];

  const searchableTechnologies = useMemo(() => {
    if (!technologyData) {
      return [];
    }

    return technologyData.categories.flatMap((category) =>
      category.technologies.map((technology) => ({
        ...technology,
        categoryKey: category.key,
        categoryLabel: category.label,
      }))
    );
  }, [technologyData]);

  const searchResults = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    if (normalizedQuery === "") {
      return [];
    }

    return searchableTechnologies
      .filter((technology) =>
        technology.name.toLowerCase().includes(normalizedQuery)
      )
      .sort((a, b) => {
        const aStartsWith = a.name
          .toLowerCase()
          .startsWith(normalizedQuery);
        const bStartsWith = b.name
          .toLowerCase()
          .startsWith(normalizedQuery);

        if (aStartsWith !== bStartsWith) {
          return aStartsWith ? -1 : 1;
        }

        return a.name.localeCompare(
          b.name,
          "en",
          {
            sensitivity: "base",
          }
        );
      })
      .slice(0, 8);
  }, [searchQuery, searchableTechnologies]);

  const selectedTechnologies = useMemo(() => {
    const technologyByIndex = new Map(
      searchableTechnologies.map((technology) => [
        technology.index,
        technology,
      ])
    );

    const toSelectedTechnology = (index, source) => {
      const technology = technologyByIndex.get(index);

      if (!technology) {
        return null;
      }

      return {
        ...technology,
        source,
        canRemove: activeTab === "base" || source !== "base",
      };
    };

    const baseTechnologies = selectedBase
      .map((index) => toSelectedTechnology(index, "base"))
      .filter(Boolean)
      .sort((a, b) =>
        a.name.localeCompare(
          b.name,
          "en",
          {
            sensitivity: "base",
          }
        )
      );

    if (activeTab === "base") {
      return baseTechnologies;
    }

    const patternTechnologies = (selectedPatterns[activeTab] ?? [])
      .map((index) => toSelectedTechnology(index, activeTab))
      .filter(Boolean)
      .sort((a, b) =>
        a.name.localeCompare(
          b.name,
          "en",
          {
            sensitivity: "base",
          }
        )
      );

    return [
      ...baseTechnologies,
      ...patternTechnologies,
    ];
  }, [
    activeTab,
    searchableTechnologies,
    selectedBase,
    selectedPatterns,
  ]);

  const handleSearchResultClick = (technology) => {
    setSelectedCategoryKey(technology.categoryKey);
    onToggle(technology.index);
    setHighlightedTechnologyIndex(technology.index);
    setSearchQuery("");
    setIsSearchFocused(true);

    requestAnimationFrame(() => {
      searchInputRef.current?.focus();
    });

    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }

    highlightTimeoutRef.current = setTimeout(() => {
      setHighlightedTechnologyIndex(null);
      highlightTimeoutRef.current = null;
    }, 2400);
  };

  return (
    <div className="technology-panel">
      <h2 className="title is-4">
        {activeTab === "base"
          ? "現在使っている技術を選択"
          : `学習プラン ${activeTab} に追加する技術を選択`}
      </h2>

      <div className="tabs is-toggle">
        <ul>
          <li className={activeTab === "base" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("base")}>
              現在の技術
            </a>
          </li>

          <li className={activeTab === "A" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("A")}>
              学習プラン A
            </a>
          </li>

          <li className={activeTab === "B" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("B")}>
              学習プラン B
            </a>
          </li>

          <li className={activeTab === "C" ? "is-active" : ""}>
            <a onClick={() => setActiveTab("C")}>
              学習プラン C
            </a>
          </li>
        </ul>
      </div>

      {technologyData ? (
        <>
          <div className="selected-technologies">
            <div className="selected-technologies-header">
              <span className="label mb-0">
                選択中の技術
              </span>

              <span className="selected-technologies-count">
                {selectedTechnologies.length}
              </span>
            </div>

            {selectedTechnologies.length > 0 ? (
              <div className="tags selected-technologies-tags">
                {selectedTechnologies.map((technology) => (
                  <span
                    key={technology.index}
                    className={[
                      "tag",
                      "selected-technology-tag",
                      `is-selected-${technology.source.toLowerCase()}`,
                    ].join(" ")}
                  >
                    <button
                      type="button"
                      className="selected-technology-name"
                      onClick={() =>
                        setSelectedCategoryKey(technology.categoryKey)
                      }
                    >
                      {technology.name}
                    </button>

                    {technology.canRemove && (
                      <button
                        type="button"
                        className="delete is-small"
                        aria-label={`${technology.name}を解除`}
                        onClick={() => onToggle(technology.index)}
                      />
                    )}
                  </span>
                ))}
              </div>
            ) : (
              <p className="selected-technologies-empty">
                まだ選択されていません
              </p>
            )}
          </div>

          <div className="columns is-variable is-3">
            <div className="column is-one-third">
              <div className="field">
                <label
                  className="label"
                  htmlFor="technology-category-select"
                >
                  技術ジャンル
                </label>

                <div className="control">
                  <div className="select is-fullwidth">
                    <select
                      id="technology-category-select"
                      value={selectedCategoryKey}
                      onChange={(event) =>
                        setSelectedCategoryKey(event.target.value)
                      }
                    >
                      {technologyData.categories.map((category) => (
                        <option
                          key={category.key}
                          value={category.key}
                        >
                          {category.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div className="column is-one-third">
              <div className="field technology-search">
                <label
                  className="label"
                  htmlFor="technology-search-input"
                >
                  検索
                </label>

                <div className="control">
                  <input
                    ref={searchInputRef}
                    id="technology-search-input"
                    className="input"
                    type="search"
                    value={searchQuery}
                    placeholder="技術名を検索"
                    autoComplete="off"
                    onChange={(event) =>
                      setSearchQuery(event.target.value)
                    }
                    onFocus={() => setIsSearchFocused(true)}
                    onBlur={() => setIsSearchFocused(false)}
                  />
                </div>

                {isSearchFocused && searchQuery.trim() !== "" && (
                  <div className="technology-search-results">
                    {searchResults.length > 0 ? (
                      searchResults.map((technology) => (
                        <button
                          key={technology.index}
                          type="button"
                          className="technology-search-result"
                          onMouseDown={(event) => {
                            event.preventDefault();
                            handleSearchResultClick(technology);
                          }}
                        >
                          <span>{technology.name}</span>
                          <span className="technology-search-category">
                            {technology.categoryLabel}
                          </span>
                        </button>
                      ))
                    ) : (
                      <div className="technology-search-empty">
                        該当する技術がありません
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <TechnologySelector
            categories={visibleCategories}
            mode={activeTab}
            baseSelected={selectedBase}
            patternSelected={
              activeTab === "base"
                ? []
                : selectedPatterns[activeTab]
            }
            highlightedTechnologyIndex={highlightedTechnologyIndex}
            onToggle={onToggle}
          />
        </>
      ) : (
        <p>技術データを読み込んでいます...</p>
      )}
    </div>
  );
}
