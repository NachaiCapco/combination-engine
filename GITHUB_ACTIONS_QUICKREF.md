# 🚀 TestForge GitHub Actions - Quick Reference

## ⚡ Quick Commands

### **Run Full Integration Test**
```bash
gh workflow run api-integration-test.yml -f testName=my-test
```

### **Run Individual Actions**
```bash
# 1. Download example template
gh workflow run action-1-download-example.yml

# 2. Generate combinations (choose one method)

  # Method A: From committed file
  gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx

  # Method B: From external URL (S3, Google Drive, Dropbox)
  gh workflow run action-2-combination-from-url.yml -f fileUrl="https://..."

  # Method C: From GitHub Issue (attach file to issue with label "testforge-upload")

  # Method D: Using S3 helper script
  ./tools/s3-upload-helper.sh your-file.xlsx

# 3. Compile tests
gh workflow run action-3-compile.yml -f testName=suite -f inputFile=data/filled.xlsx

# 4. Run tests
gh workflow run action-4-run-stream.yml -f testName=suite

# 5. Download report
gh workflow run action-5-download-report.yml -f testName=suite
```

---

## 📊 Monitor Workflows

```bash
# List recent runs
gh run list --workflow=api-integration-test.yml

# Watch live
gh run watch

# View specific run
gh run view <RUN_ID>

# Download artifacts
gh run download <RUN_ID>
```

---

## 🔧 Common Inputs

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `testName` | Test suite name | `github-action-test` | `staging-smoke` |
| `inputFile` | Path to input file | uses example | `data/tests.xlsx` |
| `timestamp` | Report timestamp | latest | `20251030_143022` |

---

## 📦 Artifacts

| Workflow | Artifact Name | Retention |
|----------|---------------|-----------|
| Integration Test | `testforge-reports-{testName}` | 30 days |
| Download Example | `example-template` | 7 days |
| Generate Combos | `test-combinations` | 14 days |
| Compile Tests | `compiled-tests-{testName}` | 30 days |
| Run Stream | `test-stream-output-{testName}` | 14 days |
| Download Report | `test-report-{testName}` | 30 days |

---

## 🐛 Troubleshooting

### **Check Server Logs**
```bash
# Download artifacts and check server.log
gh run download <RUN_ID>
cat testforge-reports-*/server.log
```

### **Check SSE Output**
```bash
# View streaming test execution
cat testforge-reports-*/sse_output.log
```

### **Re-run Failed Workflow**
```bash
gh run rerun <RUN_ID>
```

---

## 📤 File Upload Methods

GitHub Actions doesn't support direct file uploads via web UI. Choose one method:

### **Method 1: Commit to Repository** (Simplest)
```bash
mkdir -p data
cp your-file.xlsx data/input.xlsx
git add data/input.xlsx
git commit -m "Add test data"
git push

gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx
```
**Best for:** Small-medium files, version control, team collaboration

### **Method 2: GitHub Issues** (No Coding)
```bash
# 1. Create issue: https://github.com/your-repo/issues/new
# 2. Add label: "testforge-upload"
# 3. Drag & drop XLSX/CSV file into issue body
# 4. Submit issue (workflow auto-triggers)
```
**Best for:** Manual testing, medium files (<25MB), simple workflow

### **Method 3: External URL** (Large Files)
```bash
# Upload to S3/Google Drive/Dropbox first, then:
gh workflow run action-2-combination-from-url.yml \
  -f fileUrl="https://your-file-url"
```
**Best for:** Large files, automation, temporary processing

### **Method 4: S3 Helper Script** (Automated)
```bash
# Upload and trigger in one command
./tools/s3-upload-helper.sh your-file.xlsx
```
**Best for:** Large files, automation, presigned URLs

### **Method 5: Web UI** (Quick Testing)
```bash
# Open web interface
open tools/upload-trigger.html
# Fill form and upload (max ~180KB)
```
**Best for:** Small files, quick ad-hoc testing

📚 **Detailed Guide:** [tools/FILE_UPLOAD_GUIDE.md](tools/FILE_UPLOAD_GUIDE.md)

---

## 🎯 Best Practices

✅ Use descriptive `testName` values (e.g., `api-smoke-test`, `regression-suite`)  
✅ Store input files in `data/` directory  
✅ Download artifacts immediately after run completion  
✅ Review `compile_response.json` for compilation details  
✅ Check `sse_output.log` for test execution progress  
✅ Use timestamp parameter for specific report downloads  

---

**Full Documentation:** [.github/workflows/README.md](.github/workflows/README.md)
