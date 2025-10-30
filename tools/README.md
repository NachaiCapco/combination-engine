# 🛠️ TestForge Tools

Utilities and helpers for TestForge file upload and workflow management.

---

## 📁 Files in This Directory

### 1. `upload-trigger.html` - Web UI File Upload
Interactive web interface for uploading files via GitHub API (base64 encoding).

**Usage:**
```bash
# Open in browser
open upload-trigger.html
```

**Features:**
- ✅ Drag & drop file upload
- ✅ Automatic base64 encoding
- ✅ Direct workflow trigger
- ⚠️ Max file size: ~180KB

---

### 2. `s3-upload-helper.sh` - AWS S3 Upload Script
Bash script to upload files to S3 and trigger workflows.

**Usage:**
```bash
# Basic upload
./s3-upload-helper.sh your-file.xlsx

# Custom bucket
./s3-upload-helper.sh your-file.xlsx --bucket my-bucket

# Custom expiration (2 hours)
./s3-upload-helper.sh your-file.xlsx --expiration 7200

# Specific repository
./s3-upload-helper.sh your-file.xlsx --repo owner/repo
```

**Prerequisites:**
- AWS CLI installed and configured
- GitHub CLI installed and authenticated
- S3 bucket created

**Features:**
- ✅ Automatic S3 upload
- ✅ Presigned URL generation
- ✅ Workflow trigger
- ✅ Progress monitoring
- ✅ No file size limit

---

### 3. `FILE_UPLOAD_GUIDE.md` - Complete Documentation
Comprehensive guide covering all file upload methods.

**Contents:**
- Option 1: Base64 via Web UI (~180KB limit)
- Option 2: GitHub Issues (25MB limit)
- Option 3: External URL/S3 (unlimited)
- Option 4: Commit to Repository (100MB limit)

**Read here:** [FILE_UPLOAD_GUIDE.md](./FILE_UPLOAD_GUIDE.md)

---

## 🚀 Quick Start

### For Small Files (<180KB)
```bash
# Use web interface
open upload-trigger.html
```

### For Medium Files (<25MB)
```bash
# Create GitHub issue with label "testforge-upload"
gh issue create --label "testforge-upload" --title "Upload Test Data"
# Attach file in web UI
```

### For Large Files (>25MB)
```bash
# Use S3 helper script
./s3-upload-helper.sh large-file.xlsx

# OR upload to cloud storage manually
# Google Drive, Dropbox, etc.
# Then use:
gh workflow run action-2-combination-from-url.yml \
  -f fileUrl="https://your-url..."
```

### For Version Control
```bash
# Commit to repository
mkdir -p ../data
cp your-file.xlsx ../data/input.xlsx
git add ../data/input.xlsx
git commit -m "Add test data"
git push

gh workflow run action-2-combination.yml -f inputFile=data/input.xlsx
```

---

## 📊 Comparison

| Method | Max Size | Setup | Best For |
|--------|----------|-------|----------|
| Web UI | ~180KB | 5 min | Quick tests |
| Issues | 25MB | 2 min | Manual testing |
| S3/URL | Unlimited | 10 min | Large files, automation |
| Commit | 100MB | 1 min | Version control |

---

## 🔐 Security Notes

### Never Upload Files Containing:
- ❌ API keys or tokens
- ❌ Passwords or credentials
- ❌ Personal identifiable information (PII)
- ❌ Production database dumps

### Best Practices:
- ✅ Use sample/mock data for testing
- ✅ Revoke temporary URLs after use
- ✅ Use private repositories for sensitive data
- ✅ Review files before uploading

---

## 📚 Related Documentation

- [GitHub Actions Workflows](../.github/workflows/README.md)
- [Quick Reference](../GITHUB_ACTIONS_QUICKREF.md)
- [Main README](../README.md)
- [PRD](../PRD.md)

---

## 🆘 Troubleshooting

### Web UI Issues

**Problem:** "File too large"
```
Solution: File exceeds 180KB limit. Use S3 upload or commit to repo instead.
```

**Problem:** "Failed to trigger workflow"
```
Solution: Check GitHub token has 'repo' scope. Regenerate if needed.
```

### S3 Upload Issues

**Problem:** "AWS CLI not found"
```bash
# macOS
brew install awscli

# Linux
pip install awscli

# Configure
aws configure
```

**Problem:** "Bucket not found"
```bash
# Create bucket
aws s3 mb s3://testforge-uploads

# Or specify existing bucket
./s3-upload-helper.sh file.xlsx --bucket my-existing-bucket
```

### GitHub Issues Method

**Problem:** "Workflow not triggered"
```
Solution: Ensure issue has label "testforge-upload" exactly (case-sensitive)
```

**Problem:** "File not downloaded"
```
Solution: Check file URL is accessible. GitHub attachment URLs require authentication.
```

---

## 💡 Tips & Tricks

### 1. Batch Upload with S3
```bash
# Upload multiple files
for file in data/*.xlsx; do
    ./s3-upload-helper.sh "$file" --test-id "batch-$(basename $file .xlsx)"
done
```

### 2. Automated Testing Pipeline
```bash
# 1. Upload to S3
URL=$(./s3-upload-helper.sh test.xlsx | grep "https://" | tail -n 1)

# 2. Wait for workflow
gh run watch

# 3. Download results
gh run download
```

### 3. Use Environment Variables
```bash
# Set defaults
export S3_BUCKET=my-testforge-bucket
export GITHUB_REPO=myorg/myrepo

# Then simply:
./s3-upload-helper.sh file.xlsx
```

### 4. Generate Shareable Links
```bash
# Google Drive
Original: https://drive.google.com/file/d/FILE_ID/view
Direct:   https://drive.google.com/uc?export=download&id=FILE_ID

# Dropbox
Original: https://www.dropbox.com/s/xxxxx/file.xlsx?dl=0
Direct:   https://www.dropbox.com/s/xxxxx/file.xlsx?dl=1
```

---

## 🎯 Recommended Workflow

### Development/Testing (Small Files)
```
Use: Web UI (upload-trigger.html)
Why: Fastest, no setup needed
```

### Manual Testing (Medium Files)
```
Use: GitHub Issues
Why: Simple, no coding required
```

### Production/CI/CD (Any Size)
```
Use: S3 Upload Script
Why: Automated, reliable, unlimited size
```

### Team Collaboration
```
Use: Commit to Repository
Why: Version controlled, reviewable
```

---

## 📞 Support

For issues or questions:
1. Check [FILE_UPLOAD_GUIDE.md](./FILE_UPLOAD_GUIDE.md)
2. Review workflow logs: `gh run view --log`
3. Check GitHub Actions tab for error messages

---

**Last Updated:** October 30, 2025
**TestForge Version:** 1.0
