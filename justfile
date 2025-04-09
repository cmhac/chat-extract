test: 
    pytest $(jq -r '.["python.testing.pytestArgs"] | join(" ")' .vscode/settings.json)
    pylint chat_extract
    black --check chat_extract
    coverage report
    just genbadges

genbadges:
    genbadge tests -i report.xml -o docs/badge/tests-badge.svg
    genbadge coverage -i coverage.xml -o docs/badge/coverage-badge.svg

tag:
    ./scripts/auto-tag.sh