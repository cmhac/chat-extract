#!/usr/bin/env bash

# Use poetry's python API to get the new version
NEW_VER=$(poetry version -s)

# Fetch tags
git fetch --prune --tags

# Check if tag already exists
EXISTING_VERSIONS=$(git tag --list)

if [[ $EXISTING_VERSIONS =~ (^|[[:space:]])"$NEW_VER"($|[[:space:]]) ]]; then
    echo "Tag $NEW_VER already exists. Skipping..."
    exit 0
else
    git config --global user.name 'Christopher Hacker'
    git config --global user.email 'christopher-hacker@users.noreply.github.com'
    echo "Creating tag $NEW_VER..."
    git tag $NEW_VER
    git push origin $NEW_VER
    echo "NEW_VER=$NEW_VER" >>"$GITHUB_ENV"
fi
