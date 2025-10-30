# TestForge GitHub Actions Workflows

This directory contains GitHub Actions workflows for automating TestForge API testing pipeline.

## 📋 Available Workflows

### 🔄 Full Integration Test
**File:** `api-integration-test.yml`

Runs the complete TestForge pipeline from template download to report generation.

**Usage:**
```bash
gh workflow run api-integration-test.yml -f testName=my-test
```

**What it does:**
1. Downloads example template (or uses provided input file)
2. Generates test combinations via API
3. Compiles test cases to Robot Framework
4. Executes tests with SSE streaming
5. Downloads final test report as ZIP

**Triggers:**
- Manual (`workflow_dispatch`)
- Push to `main` branch (when app code changes)
- Pull requests to `main`

---

### 📥 Action 1: Download Example Template
**File:** `action-1-download-example.yml`

Downloads the example combination data template.

**Usage:**
```bash
gh workflow run action-1-download-example.yml
```

**Artifacts:**
- `example-template/example-combination-data.xlsx` (7 days retention)

---

### 🔀 Action 2: Generate Test Combinations
**File:** `action-2-combination.yml`

Generates all possible test combinations from input XLSX/CSV file.

**Usage:**
```bash
gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx
```

**Parameters:**
| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `inputFile` | No | `data/example-input.xlsx` | Path to input XLSX/CSV file |

**Prerequisites:**
1. Your input XLSX/CSV file must be committed to the repository in the `data/` directory
2. File should contain columns like `[API]endpoint`, `[API]Method`, `[Request][Header]*`, etc.

**How to add your input file:**
```bash
# 1. Create data directory (if it doesn't exist)
mkdir -p data

# 2. Place your file
cp your-input.xlsx data/input.xlsx

# 3. Commit to repository
git add data/input.xlsx
git commit -m "Add test input file"
git push
```

**Artifacts:**
- `test-combinations/combination_testcases.xlsx` (14 days retention)
- `combination-server-logs/server.log` (7 days retention)

---

### ⚙️ Action 3: Compile Test Cases
**File:** `action-3-compile.yml`

Compiles filled Excel file with expected results into Robot Framework test scripts.

**Usage:**
```bash
gh workflow run action-3-compile.yml \
  -f testName=my-suite \
  -f inputFile=data/filled.xlsx
```

**Parameters:**
| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `testName` | Yes | `github-action-test` | Test suite name (alphanumeric + underscore only) |
| `inputFile` | No | `data/combination-filled.xlsx` | Path to filled XLSX with `[Response]` columns |

**Prerequisites:**
1. Download `combination_testcases.xlsx` from Action 2
2. Manually add `[Response]` columns (e.g., `[Response][API]status`, `[Response][Body]data.hasdata`)
3. Save as `data/filled.xlsx` or similar
4. Commit to repository:
   ```bash
   git add data/filled.xlsx
   git commit -m "Add filled test cases with expected results"
   git push
   ```

**Artifacts:**
- `compiled-tests-{testName}/workspace/{testName}/` (30 days retention)
- `compiled-tests-{testName}/compile_response.json`
- `compile-server-logs/server.log` (7 days retention)

---

### ▶️ Action 4: Run Tests (SSE Stream)
**File:** `action-4-run-stream.yml`

Executes Robot Framework tests with real-time SSE streaming.

**Usage:**
```bash
gh workflow run action-4-run-stream.yml -f testName=my-suite
```

**Parameters:**
| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `testName` | Yes | `github-action-test` | Test suite name to execute |

**Prerequisites:**
- Test suite must be compiled first (Action 3)
- Workspace directory `workspace/{testName}/generated/` must exist with `.robot` files

**Artifacts:**
- `test-stream-output-{testName}/workspace/{testName}/Report/` (14 days retention)
- `test-stream-output-{testName}/sse_output.log`
- `run-server-logs/server.log` (7 days retention)

---

### 📦 Action 5: Download Test Report
**File:** `action-5-download-report.yml`

Downloads test execution report as ZIP file.

**Usage:**
```bash
# Download latest report
gh workflow run action-5-download-report.yml -f testName=my-suite

# Download specific report by timestamp
gh workflow run action-5-download-report.yml \
  -f testName=my-suite \
  -f timestamp=2025-10-30_14-30-22
```

**Parameters:**
| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `testName` | Yes | `github-action-test` | Test suite name |
| `timestamp` | No | (empty = latest) | Report timestamp in format `YYYY-MM-DD_HH-MM-SS` |

**Prerequisites:**
- Test suite must have been executed at least once (Action 4)
- Report directory must exist in `workspace/{testName}/Report/`

**Artifacts:**
- `test-report-{testName}/{testName}_Report_{timestamp}.zip` (30 days retention)
- `test-report-{testName}/extracted_report/` (unzipped contents)
- `download-server-logs/server.log` (7 days retention)

---

## 🚀 Quick Start Guide

### Complete Workflow (All Steps)

```bash
# Run full integration test
gh workflow run api-integration-test.yml -f testName=my-integration-test

# Monitor progress
gh run watch

# Download artifacts when complete
gh run download
```

### Individual Steps Workflow

**Step 1: Get Example Template**
```bash
gh workflow run action-1-download-example.yml
gh run download
```

**Step 2: Add Your Input File**
```bash
# Download the example template from artifacts
# Modify it with your test data
# Save as data/input.xlsx

mkdir -p data
cp ~/Downloads/example-combination-data.xlsx data/input.xlsx

git add data/input.xlsx
git commit -m "Add test input"
git push
```

**Step 3: Generate Combinations**
```bash
gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx
gh run watch
gh run download
```

**Step 4: Fill Expected Results**
```bash
# Download combination_testcases.xlsx from artifacts
# Open in Excel/Numbers
# Add [Response] columns:
#   - [Response][API]status (e.g., 200, 404)
#   - [Response][Body]data.hasdata (e.g., true)
#   - [Response][Header]x-token (e.g., abc123)
# Save as data/filled.xlsx

git add data/filled.xlsx
git commit -m "Add expected results"
git push
```

**Step 5: Compile Tests**
```bash
gh workflow run action-3-compile.yml \
  -f testName=my-suite \
  -f inputFile=data/filled.xlsx

gh run watch
```

**Step 6: Run Tests**
```bash
gh workflow run action-4-run-stream.yml -f testName=my-suite
gh run watch
```

**Step 7: Download Report**
```bash
gh workflow run action-5-download-report.yml -f testName=my-suite
gh run download
```

---

## 📁 File Upload Process

Since GitHub Actions cannot directly upload files through the web UI, you need to:

### Option A: Commit Files to Repository
```bash
# 1. Create data directory
mkdir -p data

# 2. Add your test files
cp your-input.xlsx data/input.xlsx
cp your-filled.xlsx data/filled.xlsx

# 3. Commit and push
git add data/
git commit -m "Add test data files"
git push
```

### Option B: Use Example Template (Automated)
```bash
# The integration test automatically downloads the example template
gh workflow run api-integration-test.yml
```

---

## 📊 Monitoring Workflows

### List Recent Runs
```bash
gh run list --workflow=api-integration-test.yml
```

### Watch Live Execution
```bash
gh run watch
```

### View Specific Run
```bash
gh run view <RUN_ID>
```

### View Logs
```bash
gh run view <RUN_ID> --log
```

### Download Artifacts
```bash
# Download all artifacts from latest run
gh run download

# Download from specific run
gh run download <RUN_ID>
```

### Re-run Failed Workflow
```bash
gh run rerun <RUN_ID>
```

---

## 🐛 Troubleshooting

### Server Failed to Start
**Check server logs:**
```bash
gh run download <RUN_ID>
cat testforge-reports-*/server.log
```

**Common causes:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- Port 3000 already in use

### Input File Not Found
**Error:** `Input file 'data/input.xlsx' not found!`

**Solution:**
```bash
# Ensure file is committed to repository
git add data/input.xlsx
git commit -m "Add input file"
git push
```

### Test Suite Not Found
**Error:** `Test suite 'my-suite' not found!`

**Solution:**
Run Action 3 (Compile) first:
```bash
gh workflow run action-3-compile.yml -f testName=my-suite -f inputFile=data/filled.xlsx
```

### Invalid Test Name
**Error:** `testName must contain only alphanumeric characters and underscores`

**Valid names:** `my_test`, `suite_1`, `API_Test_v2`
**Invalid names:** `my-test`, `suite.1`, `API Test`

### SSE Timeout
**Error:** `Test execution timeout (10 minutes)`

**Possible causes:**
- Too many test cases (>100)
- API under test is slow/unresponsive
- Network issues

**Solution:** Split into smaller test suites

---

## 🎯 Best Practices

### ✅ Do's
- Use descriptive `testName` values (e.g., `api-smoke-test`, `regression-suite`)
- Store input files in `data/` directory
- Download artifacts immediately after run completion
- Review `compile_response.json` for compilation details
- Check `sse_output.log` for test execution progress
- Use timestamp parameter for specific report downloads
- Keep test suites under 100 cases for better performance

### ❌ Don'ts
- Don't use special characters in `testName` (only `a-zA-Z0-9_`)
- Don't commit sensitive data in test files (API keys, passwords)
- Don't run multiple tests with same `testName` simultaneously
- Don't forget to add `[Response]` columns before compiling
- Don't use paths outside the repository for `inputFile`

---

## 📦 Artifacts Retention

| Artifact | Retention Period |
|----------|------------------|
| Full integration test results | 30 days |
| Example template | 7 days |
| Test combinations | 14 days |
| Compiled tests | 30 days |
| Test execution output | 14 days |
| Test reports | 30 days |
| Server logs | 7 days |

---

## 🔐 Security Notes

- Never commit `.env` files with secrets
- Use GitHub Secrets for sensitive data
- Review uploaded files for sensitive information
- Limit workflow permissions to minimum required

---

## 📚 Related Documentation

- [Main README](../../README.md)
- [PRD Documentation](../../PRD.md)
- [Quick Reference](../../GITHUB_ACTIONS_QUICKREF.md)
- [Robot Framework Docs](https://robotframework.org/)
- [GitHub CLI Docs](https://cli.github.com/manual/)

---

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review workflow logs: `gh run view <RUN_ID> --log`
3. Download artifacts for detailed error messages
4. Check server logs in artifacts

---

**Last Updated:** October 30, 2025
**TestForge Version:** 1.0
