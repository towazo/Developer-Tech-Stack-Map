export default function TechnologySelector({
  categories,
  mode,
  baseSelected,
  patternSelected,
  highlightedTechnologyIndex,
  onToggle,
}) {
  return (
    <div>
      {categories.map((category) => (
        <div key={category.key} className="mb-5">

          <div className="buttons">

            {[...category.technologies]
              .sort((a, b) =>
                a.name.localeCompare(
                  b.name,
                  "en",
                  {
                    sensitivity: "base",
                  }
                )
              )
              .map((technology) => {

              const isBaseSelected =
                baseSelected.includes(technology.index);

              const isPatternSelected =
                patternSelected.includes(technology.index);

              let buttonClass = "button is-small";

              // Baseで選択済み
              if (isBaseSelected) {
                buttonClass += " is-info";
              }

              // Patternで追加
              else if (isPatternSelected) {

                if (mode === "A") {
                  buttonClass += " is-warning";
                }

                if (mode === "B") {
                  buttonClass += " is-success";
                }

                if (mode === "C") {
                  buttonClass += " is-danger";
                }
              }

              if (highlightedTechnologyIndex === technology.index) {
                buttonClass += " is-search-highlighted";
              }

              return (
                <button
                  key={technology.index}
                  className={buttonClass}
                  onClick={() => onToggle(technology.index)}
                >
                  {technology.name}
                </button>
              );
            })}

          </div>
        </div>
      ))}
    </div>
  );
}
