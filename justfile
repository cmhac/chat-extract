test:
    pytest $(jq -r '.["python.testing.pytestArgs"] | join(" ")' .vscode/settings.json)