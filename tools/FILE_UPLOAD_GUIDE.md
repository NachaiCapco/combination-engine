# 📤 File Upload Options for GitHub Actions

Since GitHub Actions workflows don't have a native "file upload" UI, here are **4 practical solutions** to upload files and trigger workflows.

---

## 📊 Comparison Table

| Method | Max File Size | Complexity | Best For | Setup Time |
|--------|--------------|------------|----------|------------|
| **Option 1: Base64 via Web UI** | ~180KB | Medium | Small files, quick testing | 5 min |
| **Option 2: GitHub Issues** | 25MB | Easy | Medium files, manual testing | 2 min |
| **Option 3: External URL (S3/GCS)** | Unlimited | Medium | Large files, automation | 10 min |
| **Option 4: Commit to Repo** | 100MB | Easy | Any size, version control | 1 min |

---

## 🎯 Option 1: Web UI with Base64 Encoding

**Best for:** Small files (<180KB), quick ad-hoc testing

### How It Works
1. Upload file through web interface
2. File is base64-encoded and sent via GitHub API
3. Workflow decodes and processes the file

### Setup

**Step 1: Create GitHub Personal Access Token**
```
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "TestForge Upload"
4. Scopes: ✅ repo (all)
5. Click "Generate token"
6. Copy token (ghp_xxxxxxxxxxxx)
```

**Step 2: Open the Web Interface**
```bash
# Open the HTML file in your browser
open tools/upload-trigger.html
```

**Step 3: Fill in the form**
```
GitHub Token: ghp_xxxxxxxxxxxx
Repository Owner: your-username
Repository Name: PruJourney-SG
Test ID: test-001 (optional)
File: Choose your XLSX/CSV file
```

**Step 4: Click "Upload & Trigger Workflow"**

**Step 5: Monitor workflow**
```bash
gh run list
gh run watch
```

### Workflow File
`.github/workflows/action-2-combination-with-upload.yml`

### Limitations
- ❌ Max ~180KB (GitHub API payload limit)
- ❌ Requires GitHub token
- ❌ No direct feedback (must check Actions tab)

### Usage Example
```bash
# Just open the HTML file and upload through browser
open tools/upload-trigger.html
```

---

## 🐙 Option 2: GitHub Issues (Recommended for Manual Testing)

**Best for:** Medium files (<25MB), manual workflow, no code needed

### How It Works
1. Create GitHub Issue
2. Attach XLSX/CSV file to issue
3. Add special label to trigger workflow
4. Workflow downloads file and processes it

### Setup

**Step 1: Create a new issue**
```
1. Go to: https://github.com/your-username/PruJourney-SG/issues/new
2. Title: "Generate Test Combinations - [Your Test Name]"
3. Body: Drag and drop your XLSX/CSV file
4. Labels: Add "testforge-upload"
5. Click "Submit new issue"
```

**Step 2: Wait for workflow to complete**
- Workflow automatically triggers when issue is created with label
- Check Actions tab for progress
- Bot will comment on issue with artifact link

**Step 3: Download results**
```
1. Click on Actions tab
2. Find the workflow run
3. Download artifact: test-combinations-issue-{number}
```

### Workflow File
`.github/workflows/action-2-combination-from-issue.yml`

### Example Issue Template

**Title:** Generate Test Combinations - User Registration API

**Body:**
```markdown
## Test Data Upload

Uploading input file for test combination generation.

**Test Name:** user_registration_tests
**API Under Test:** /api/v1/users/register
**Expected Combinations:** ~50

[Attach your XLSX/CSV file by dragging here]
```

**Labels:** `testforge-upload`

### Advantages
✅ Simple - no coding required
✅ Up to 25MB file size
✅ Automatic workflow trigger
✅ Bot comments with results
✅ Issue serves as documentation

### Limitations
❌ Requires manual issue creation
❌ Public repos expose files
❌ Clutters issue tracker

### Usage Example
```bash
# Using GitHub CLI
gh issue create \
  --title "Generate Combinations - API Test" \
  --label "testforge-upload" \
  --body "See attached file"

# Then manually attach file in web UI
```

---

## ☁️ Option 3: External Storage URL (Best for Large Files)

**Best for:** Large files, automation, CI/CD integration

### How It Works
1. Upload file to cloud storage (S3, Google Drive, Dropbox, etc.)
2. Get public/presigned URL
3. Trigger workflow with URL
4. Workflow downloads and processes file

### Setup

#### Option 3A: AWS S3 (Recommended)

**Step 1: Upload to S3**
```bash
# Install AWS CLI
brew install awscli  # macOS
# or
pip install awscli

# Configure AWS
aws configure

# Upload file
aws s3 cp your-file.xlsx s3://your-bucket/testforge/input.xlsx
```

**Step 2: Generate presigned URL**
```bash
# Generate URL valid for 1 hour
aws s3 presign s3://your-bucket/testforge/input.xlsx --expires-in 3600
```

**Step 3: Trigger workflow**
```bash
gh workflow run action-2-combination-from-url.yml \
  -f fileUrl="https://your-bucket.s3.amazonaws.com/..." \
  -f testId="s3-upload-001"
```

#### Option 3B: Google Drive

**Step 1: Upload to Google Drive**
```
1. Upload file to Google Drive
2. Right-click → Share → Anyone with link can view
3. Copy link: https://drive.google.com/file/d/{FILE_ID}/view
```

**Step 2: Convert to direct download link**
```
Original: https://drive.google.com/file/d/1A2B3C4D5E6F/view
Direct:   https://drive.google.com/uc?export=download&id=1A2B3C4D5E6F
```

**Step 3: Trigger workflow**
```bash
gh workflow run action-2-combination-from-url.yml \
  -f fileUrl="https://drive.google.com/uc?export=download&id=1A2B3C4D5E6F" \
  -f testId="gdrive-upload-001"
```

#### Option 3C: Dropbox

**Step 1: Upload to Dropbox**
```
1. Upload file to Dropbox
2. Right-click → Share → Create link
3. Copy link: https://www.dropbox.com/s/xxxxx/file.xlsx?dl=0
```

**Step 2: Convert to direct download**
```
Original: https://www.dropbox.com/s/xxxxx/file.xlsx?dl=0
Direct:   https://www.dropbox.com/s/xxxxx/file.xlsx?dl=1
         (change dl=0 to dl=1)
```

**Step 3: Trigger workflow**
```bash
gh workflow run action-2-combination-from-url.yml \
  -f fileUrl="https://www.dropbox.com/s/xxxxx/file.xlsx?dl=1" \
  -f testId="dropbox-upload-001"
```

### Workflow File
`.github/workflows/action-2-combination-from-url.yml`

### Advantages
✅ Unlimited file size
✅ Works with any cloud storage
✅ Good for automation
✅ Temporary URLs (presigned)
✅ No GitHub storage used

### Limitations
❌ Requires cloud storage account
❌ URL management needed
❌ Security considerations for public URLs

---

## 📁 Option 4: Commit to Repository (Default)

**Best for:** Version control, reproducibility, any file size

### How It Works
1. Add file to repository
2. Commit and push
3. Trigger workflow with file path

### Setup

**Step 1: Add file to repo**
```bash
mkdir -p data
cp your-file.xlsx data/input.xlsx
```

**Step 2: Commit and push**
```bash
git add data/input.xlsx
git commit -m "Add test input file"
git push
```

**Step 3: Trigger workflow**
```bash
gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx
```

### Advantages
✅ Simplest method
✅ Version controlled
✅ Reproducible
✅ No external dependencies

### Limitations
❌ Files are public (in public repos)
❌ Increases repo size
❌ Not suitable for sensitive data

---

## 🎯 Decision Guide

### Choose **Option 1 (Web UI)** if:
- ✅ File is small (<180KB)
- ✅ You want a quick web interface
- ✅ One-time or ad-hoc testing

### Choose **Option 2 (GitHub Issues)** if:
- ✅ File is medium size (<25MB)
- ✅ You want simplicity (no coding)
- ✅ You want workflow history in issues
- ✅ Manual testing workflow

### Choose **Option 3 (External URL)** if:
- ✅ File is large (>25MB)
- ✅ You have cloud storage already
- ✅ You need automation/CI/CD
- ✅ Temporary file processing

### Choose **Option 4 (Commit)** if:
- ✅ You want version control
- ✅ File needs to be shared with team
- ✅ Reproducibility is important
- ✅ File is not sensitive

---

## 🔐 Security Best Practices

### For All Options:
- ❌ **Never upload files with API keys, passwords, or secrets**
- ✅ Use `.env` files or GitHub Secrets for credentials
- ✅ Review files before uploading
- ✅ Delete temporary URLs after use

### For Option 1 (Base64):
- ⚠️ Token has full repo access - protect it
- ✅ Use short-lived tokens
- ✅ Revoke tokens after use

### For Option 2 (Issues):
- ⚠️ Files are public in public repos
- ✅ Use private repos for sensitive data
- ✅ Close/delete issues after processing

### For Option 3 (URLs):
- ✅ Use presigned URLs with short expiration
- ✅ Revoke public links after workflow completes
- ⚠️ Be careful with permanent public URLs

### For Option 4 (Commit):
- ❌ Never commit sensitive test data
- ✅ Use `.gitignore` for sensitive files
- ✅ Consider using Git LFS for large files

---

## 🛠️ Advanced: Combine Multiple Options

### Example: Hybrid Workflow

```yaml
name: "Smart File Upload"

on:
  workflow_dispatch:
    inputs:
      uploadMethod:
        description: 'Upload method'
        required: true
        type: choice
        options:
          - commit
          - url
          - issue
      filePath:
        description: 'File path (for commit method)'
        required: false
      fileUrl:
        description: 'File URL (for url method)'
        required: false
      issueNumber:
        description: 'Issue number (for issue method)'
        required: false

jobs:
  process-file:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get file (commit method)
        if: inputs.uploadMethod == 'commit'
        run: cp ${{ inputs.filePath }} input.xlsx

      - name: Get file (URL method)
        if: inputs.uploadMethod == 'url'
        run: curl -L ${{ inputs.fileUrl }} -o input.xlsx

      - name: Get file (issue method)
        if: inputs.uploadMethod == 'issue'
        run: |
          # Extract URL from issue and download
          echo "Download from issue #${{ inputs.issueNumber }}"

      # ... rest of workflow
```

---

## 📞 Support

Need help? Check:
- [Main Workflows README](../.github/workflows/README.md)
- [GitHub Actions Quick Reference](../GITHUB_ACTIONS_QUICKREF.md)
- [PRD Documentation](../PRD.md)

---

**Last Updated:** October 30, 2025
