const PROJECTION_NEIGHBORS = 15;
const NEIGHBOR_COUNT = 500;

let runtimePromise;

function loadRuntime() {
  if (!runtimePromise) {
    runtimePromise = fetch("/data/browser_runtime.json").then((response) => {
      if (!response.ok) {
        throw new Error(`Browser runtime returned ${response.status}`);
      }
      return response.json();
    });
  }
  return runtimePromise;
}

export async function analyzeTechnologyStack(selectedIndexes, technologyData) {
  const runtime = await loadRuntime();
  const selectedSet = new Set(selectedIndexes);
  const selectedNorm = selectedIndexes.reduce(
    (sum, index) => sum + runtime.weights[index] ** 2,
    0
  );

  const originalDistances = runtime.respondents.map((respondent, index) => {
    const dotProduct = respondent[0].reduce(
      (sum, featureIndex) => selectedSet.has(featureIndex)
        ? sum + runtime.weights[featureIndex] ** 2
        : sum,
      0
    );
    return {
      index,
      distance: Math.sqrt(Math.max(selectedNorm + respondent[1] - 2 * dotProduct, 0)),
    };
  });

  originalDistances.sort((left, right) => left.distance - right.distance);
  const projectionNeighbors = originalDistances.slice(0, PROJECTION_NEIGHBORS);
  const exactMatch = projectionNeighbors.find((neighbor) => neighbor.distance === 0);

  let x;
  let y;

  if (exactMatch) {
    const respondent = runtime.respondents[exactMatch.index];
    x = respondent[2];
    y = respondent[3];
  } else {
    let totalWeight = 0;
    let weightedX = 0;
    let weightedY = 0;

    projectionNeighbors.forEach((neighbor) => {
      const respondent = runtime.respondents[neighbor.index];
      const weight = 1 / Math.max(neighbor.distance, 0.000001) ** 2;
      totalWeight += weight;
      weightedX += respondent[2] * weight;
      weightedY += respondent[3] * weight;
    });

    x = weightedX / totalWeight;
    y = weightedY / totalWeight;
  }

  const mapDistances = runtime.respondents.map((respondent, index) => ({
    index,
    distance: Math.hypot(respondent[2] - x, respondent[3] - y),
  }));
  mapDistances.sort((left, right) => left.distance - right.distance);
  const neighbors = mapDistances.slice(0, NEIGHBOR_COUNT);

  return {
    x,
    y,
    method: "browser.knnProjection",
    neighborhood: {
      basis: "umap_2d",
      count: neighbors.length,
      radius: neighbors[neighbors.length - 1].distance,
      statistics: calculateStatistics(runtime, neighbors, technologyData),
    },
  };
}

function calculateStatistics(runtime, neighbors, technologyData) {
  const technologies = technologyData.categories.flatMap((category) =>
    category.technologies.map((technology) => ({
      ...technology,
      category: category.key,
      categoryLabel: category.label,
    }))
  );
  const technologyCounts = Array(runtime.featureCount).fill(0);

  neighbors.forEach(({ index }) => {
    runtime.respondents[index][0].forEach((featureIndex) => {
      technologyCounts[featureIndex] += 1;
    });
  });

  const topTechnologies = technologies
    .map((technology) => {
      const usageRate = technologyCounts[technology.index] / neighbors.length * 100;
      return {
        rank: 0,
        category: technology.category,
        categoryLabel: technology.categoryLabel,
        name: technology.name,
        usageRate,
        overallUsageRate: technology.overallUsageRate,
        differencePoint: usageRate - technology.overallUsageRate,
      };
    })
    .sort((left, right) => right.differencePoint - left.differencePoint)
    .slice(0, 10)
    .map((technology, index) => ({ ...technology, rank: index + 1 }));

  const metadata = {};
  runtime.metadata.forEach((field, fieldIndex) => {
    const neighborCounts = Array(field.values.length).fill(0);
    const overallCounts = Array(field.values.length).fill(0);
    let neighborAnswered = 0;
    let overallAnswered = 0;

    runtime.respondents.forEach((respondent) => {
      const code = respondent[4][fieldIndex];
      if (code >= 0) {
        overallCounts[code] += 1;
        overallAnswered += 1;
      }
    });
    neighbors.forEach(({ index }) => {
      const code = runtime.respondents[index][4][fieldIndex];
      if (code >= 0) {
        neighborCounts[code] += 1;
        neighborAnswered += 1;
      }
    });

    const items = field.values
      .map((value, code) => {
        const usageRate = neighborAnswered ? neighborCounts[code] / neighborAnswered * 100 : 0;
        const overallRate = overallAnswered ? overallCounts[code] / overallAnswered * 100 : 0;
        return { value, usageRate, overallRate, differencePoint: usageRate - overallRate };
      })
      .sort((left, right) => right.differencePoint - left.differencePoint)
      .slice(0, 3)
      .map((item, index) => ({ ...item, rank: index + 1 }));

    metadata[field.key] = { label: field.label, answered: neighborAnswered, items };
  });

  const workExperience = neighbors
    .map(({ index }) => runtime.respondents[index][5])
    .filter((value) => value !== null)
    .sort((left, right) => left - right);

  return {
    count: neighbors.length,
    rate: neighbors.length / runtime.respondents.length * 100,
    topTechnologies,
    metadata,
    workExperience: {
      answered: workExperience.length,
      median: quantile(workExperience, 0.5),
      q1: quantile(workExperience, 0.25),
      q3: quantile(workExperience, 0.75),
    },
  };
}

function quantile(sortedValues, probability) {
  if (sortedValues.length === 0) {
    return 0;
  }
  const position = (sortedValues.length - 1) * probability;
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  const fraction = position - lowerIndex;
  return sortedValues[lowerIndex] * (1 - fraction) + sortedValues[upperIndex] * fraction;
}
