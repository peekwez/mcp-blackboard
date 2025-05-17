#!/bin/bash

# This script updates the badges in README.md and COVERAGE.md
# It should be run after the test coverage has been generated

# Count the number of tests
TOTAL_TESTS=$(grep -r "def test_" tests | wc -l | xargs)
echo "Total tests: ${TOTAL_TESTS}"

# Extract coverage percentage from coverage.xml
if [ -f "coverage.xml" ]; then
  COVERAGE_LINE_RATE=$(grep -o 'line-rate="[0-9.]*"' coverage.xml | head -1 | grep -o '[0-9.]*')
  COVERAGE_PCT=$(echo "${COVERAGE_LINE_RATE} * 100" | bc | xargs printf "%.0f")
  echo "Coverage from coverage.xml: ${COVERAGE_PCT}%"
elif [ -f "htmlcov/status.json" ]; then
  echo "Using htmlcov/status.json to calculate coverage"

  # Extract total and missing statements
  TOTAL=0
  MISSING=0

  for FILE in $(grep -o '"n_statements":[0-9]*' htmlcov/status.json | grep -o '[0-9]*'); do
    TOTAL=$((TOTAL + FILE))
  done

  for FILE in $(grep -o '"n_missing":[0-9]*' htmlcov/status.json | grep -o '[0-9]*'); do
    MISSING=$((MISSING + FILE))
  done

  # Calculate coverage percentage
  COVERED=$((TOTAL - MISSING))
  COVERAGE_PCT=$(echo "scale=2; (${COVERED}/${TOTAL})*100" | bc | xargs printf "%.0f")
  echo "Coverage from status.json: ${COVERAGE_PCT}%"
else
  echo "No coverage files found, using default 100%"
  COVERAGE_PCT=100
fi

# Create badge URLs
TEST_BADGE_URL="https://img.shields.io/badge/tests-${TOTAL_TESTS}%20passed-brightgreen"

# Determine badge color based on coverage percentage
COVERAGE_COLOR="red"
if (( $(echo "$COVERAGE_PCT >= 90" | bc -l) )); then
  COVERAGE_COLOR="brightgreen"
elif (( $(echo "$COVERAGE_PCT >= 80" | bc -l) )); then
  COVERAGE_COLOR="green"
elif (( $(echo "$COVERAGE_PCT >= 70" | bc -l) )); then
  COVERAGE_COLOR="yellowgreen"
elif (( $(echo "$COVERAGE_PCT >= 60" | bc -l) )); then
  COVERAGE_COLOR="yellow"
fi

COVERAGE_BADGE_URL="https://img.shields.io/badge/coverage-${COVERAGE_PCT}%25-${COVERAGE_COLOR}"

# Update README.md
echo "Updating README.md..."
# Replace existing badges if they exist
sed -i '' 's|<img src="https://img.shields.io/badge/tests-[0-9]*%20passed-[a-z]*" alt="Test Status" />|<img src="'"${TEST_BADGE_URL}"'" alt="Test Status" />|g' README.md
sed -i '' 's|<img src="https://img.shields.io/badge/coverage-[0-9]*%25-[a-z]*" alt="Coverage Status" />|<img src="'"${COVERAGE_BADGE_URL}"'" alt="Coverage Status" />|g' README.md

# If badges don't exist, add them
if ! grep -q "Test Status" README.md; then
  echo "Adding badges to README.md..."
  sed -i '' '/<div align="center">/,/<\/div>/ s|<\/div>|   <img src="'"${TEST_BADGE_URL}"'" alt="Test Status" />\n   <img src="'"${COVERAGE_BADGE_URL}"'" alt="Coverage Status" />\n</div>|g' README.md
fi

# Update COVERAGE.md
echo "Updating COVERAGE.md..."
sed -i '' "s|Overall \| [0-9]*%|Overall \| ${COVERAGE_PCT}%|g" COVERAGE.md
sed -i '' "s|![Coverage](https://img.shields.io/badge/coverage-[0-9]*%25-[a-z]*)|![Coverage](${COVERAGE_BADGE_URL})|g" COVERAGE.md
sed -i '' "s|Last updated: .*|Last updated: $(date '+%B %d, %Y')|g" COVERAGE.md
sed -i '' "s|[0-9]\+ tests passed|${TOTAL_TESTS} tests passed|g" COVERAGE.md

echo "Badges updated successfully!"
