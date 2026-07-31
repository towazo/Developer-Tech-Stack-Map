export default function TechnologySelector({
  categories,
  mode,
  baseSelected,
  patternSelected,
  onToggle,
}) {
  return (
    <div>
      {categories.map((category) => (
        <div key={category.key} className="mb-5">

          <h3 className="title is-5 mb-3">
            {category.label}
          </h3>

          <div className="buttons">

            {category.technologies.map((technology) => {

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