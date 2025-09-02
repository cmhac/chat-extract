# PyPI Publishing Setup

This document describes the setup required for publishing to PyPI.

## Trusted Publishing Configuration

The package is configured to use PyPI's trusted publishing feature, which doesn't require storing API tokens as secrets. 

### Required Setup in PyPI:

1. **Create a PyPI account** if you don't have one: https://pypi.org/account/register/
2. **Add a trusted publisher** for this repository:
   - Go to: https://pypi.org/manage/account/publishing/
   - Add a new publisher with these details:
     - **PyPI project name**: `chat-extract`
     - **Owner**: `cmhac`
     - **Repository name**: `chat-extract`
     - **Workflow filename**: `publish.yaml`
     - **Environment name**: `pypi`

### Publishing Process:

Once the trusted publisher is configured, publishing happens automatically:

1. **Version bump**: Update the version in `pyproject.toml`
2. **Create tag**: The auto-tag workflow will create a git tag when the version changes
3. **Automatic publishing**: The publish workflow triggers on tag creation and uploads to PyPI

### Manual Publishing:

If needed, you can also create a release manually on GitHub, which will trigger the publish workflow.

## First-Time Publishing

For the initial publication to PyPI:

1. Set up the trusted publisher configuration as described above
2. Make sure the version in `pyproject.toml` is correct (currently 0.2.0)
3. Create a git tag manually to trigger the first publish:
   ```bash
   git tag 0.2.0
   git push origin 0.2.0
   ```

After the first successful publish, the package will be available via:
```bash
pipx install chat-extract
```