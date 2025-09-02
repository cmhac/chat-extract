# Chat Extract

Chat Extract is a Python CLI application that extracts text messages from video recordings of chat conversations using OpenAI's vision-enabled API. The extracted messages are saved to CSV format.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
Run these commands to set up the development environment:

1. **Install Poetry and Just** (if not available):
   ```bash
   pip install poetry rust-just
   ```

2. **Install all dependencies**:
   ```bash
   poetry install
   ```
   - **TIMING**: Takes approximately 20 seconds with 148 packages
   - **NEVER CANCEL**: Set timeout to 60+ seconds for initial install

3. **Verify installation**:
   ```bash
   poetry run chat-extract --help
   ```

### Testing and Quality Assurance
Always run these commands before committing changes:

1. **Run full test suite**:
   ```bash
   poetry run pytest tests --cov --cov-report=html --cov-report=xml --junitxml=report.xml
   ```
   - **TIMING**: Takes approximately 3 seconds for 10 tests
   - **NEVER CANCEL**: Set timeout to 30+ seconds
   - **COVERAGE**: Expects 95%+ coverage, 10 tests passing

2. **Run code quality checks**:
   ```bash
   poetry run pylint chat_extract
   poetry run black --check chat_extract
   ```
   - **TIMING**: pylint takes ~8 seconds, black takes <1 second
   - **NEVER CANCEL**: Set timeout to 60+ seconds for pylint
   - **EXPECTATION**: pylint should score 10.00/10, black should show "All done!"

3. **Run all checks with Just** (badge generation will fail due to network restrictions):
   ```bash
   poetry run just test
   ```
   - **KNOWN ISSUE**: Badge generation fails with network error - this is expected and not a problem
   - The core tests, pylint, and black checks will succeed

### Running the Application

1. **Set OpenAI API Key** (required for functionality):
   ```bash
   export OPENAI_API_KEY="your_api_key_here"
   ```
   - Or create a `.env` file in the project root with: `OPENAI_API_KEY=your_api_key_here`

2. **Run chat extraction**:
   ```bash
   poetry run chat-extract VIDEO_PATH --output-path OUTPUT.csv [--n FRAMESKIP]
   ```

3. **Test with demo file**:
   ```bash
   poetry run chat-extract docs/screen-recording-example.gif --output-path test-output.csv
   ```

## Validation

### Manual Validation Requirements
After making changes, ALWAYS run through these validation scenarios:

1. **Help Command Validation**:
   ```bash
   poetry run chat-extract --help
   ```
   - Should display usage information with VIDEO_PATH argument and options

2. **Error Handling Validation**:
   ```bash
   poetry run chat-extract docs/screen-recording-example.gif
   ```
   - Without API key: Should show clear error "OPENAI_API_KEY environment variable not set"
   - With invalid API key: Should attempt processing, show progress bar, then fail with API error

3. **Code Quality Validation**:
   - Run `poetry run pylint chat_extract` - must score 10.00/10
   - Run `poetry run black --check chat_extract` - must show no changes needed
   - Run tests with full coverage reporting

4. **Package Installation Validation**:
   - Delete `.venv` if it exists: `rm -rf .venv`
   - Run clean install: `poetry install` 
   - Verify CLI works: `poetry run chat-extract --help`

5. **File Processing Validation**:
   - Test help: `poetry run chat-extract --help` should show proper usage
   - Test file loading: `poetry run chat-extract docs/screen-recording-example.gif` should fail with clear API key error
   - With API key: Should show progress bar and process frames (will fail with network error in restricted environments)

### Expected Test Results
All tests should pass without errors and achieve the required code coverage thresholds.

## Common Tasks

### Frequently Used Commands
```bash
# Development workflow
poetry install                                    # Install dependencies (~20s)
poetry run pytest tests --cov                    # Run tests (~3s)
poetry run pylint chat_extract                   # Lint code (~8s)
poetry run black chat_extract                    # Format code (<1s)

# Application usage
poetry run chat-extract --help                   # Show help
poetry run chat-extract VIDEO_PATH --output-path OUTPUT.csv

# Debugging
poetry run python -c "import chat_extract; print(chat_extract.__file__)"
```

## Critical Notes

### Timing and Cancellation Warnings
- **NEVER CANCEL**: Poetry install takes 20 seconds - set 60+ second timeout
- **NEVER CANCEL**: pylint takes 8 seconds - set 60+ second timeout  
- **NEVER CANCEL**: Tests take 3 seconds - set 30+ second timeout

### CI/CD Integration
The repository includes GitHub Actions that:
- Run on push/PR to main branch
- Use `.github/actions/setup` for Python and Poetry setup
- Execute `poetry run just test` for full validation
- Expect all code quality checks to pass

Always ensure your changes pass all local validation before pushing to avoid CI failures.