#!/bin/bash

# S3 Upload Helper for TestForge GitHub Actions
# This script uploads files to S3 and triggers the workflow

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
S3_BUCKET="${S3_BUCKET:-testforge-uploads}"
EXPIRATION_SECONDS="${EXPIRATION_SECONDS:-3600}"  # 1 hour default
GITHUB_REPO="${GITHUB_REPO:-}"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"

    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Install it first:"
        echo "  macOS:  brew install awscli"
        echo "  Linux:  pip install awscli"
        echo "  Or:     https://aws.amazon.com/cli/"
        exit 1
    fi
    print_success "AWS CLI installed"

    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI not found. Install it first:"
        echo "  macOS:  brew install gh"
        echo "  Linux:  See https://cli.github.com/"
        exit 1
    fi
    print_success "GitHub CLI installed"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run:"
        echo "  aws configure"
        exit 1
    fi
    print_success "AWS credentials configured"

    # Check GitHub auth
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI not authenticated. Run:"
        echo "  gh auth login"
        exit 1
    fi
    print_success "GitHub CLI authenticated"
}

usage() {
    cat << EOF
Usage: $0 <file-path> [options]

Upload file to S3 and trigger TestForge GitHub Actions workflow.

Options:
    -b, --bucket BUCKET       S3 bucket name (default: testforge-uploads)
    -e, --expiration SECONDS  URL expiration time (default: 3600)
    -r, --repo OWNER/REPO     GitHub repository (default: current repo)
    -t, --test-id ID          Test identifier (default: auto-generated)
    -h, --help                Show this help message

Environment Variables:
    S3_BUCKET           Default S3 bucket name
    EXPIRATION_SECONDS  Default URL expiration
    GITHUB_REPO         Default GitHub repository

Examples:
    # Upload and trigger workflow
    $0 my-test-data.xlsx

    # Upload to specific bucket
    $0 my-test-data.xlsx --bucket my-bucket

    # Upload with custom expiration (2 hours)
    $0 my-test-data.xlsx --expiration 7200

    # Upload to specific repo
    $0 my-test-data.xlsx --repo myorg/myrepo

EOF
    exit 0
}

# Parse arguments
FILE_PATH=""
TEST_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -e|--expiration)
            EXPIRATION_SECONDS="$2"
            shift 2
            ;;
        -r|--repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        -t|--test-id)
            TEST_ID="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [ -z "$FILE_PATH" ]; then
                FILE_PATH="$1"
            else
                print_error "Unknown option: $1"
                usage
            fi
            shift
            ;;
    esac
done

# Validate file path
if [ -z "$FILE_PATH" ]; then
    print_error "File path is required"
    usage
fi

if [ ! -f "$FILE_PATH" ]; then
    print_error "File not found: $FILE_PATH"
    exit 1
fi

# Get GitHub repo if not specified
if [ -z "$GITHUB_REPO" ]; then
    GITHUB_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ -z "$GITHUB_REPO" ]; then
        print_error "Could not detect GitHub repository. Use --repo option."
        exit 1
    fi
fi

# Generate test ID if not specified
if [ -z "$TEST_ID" ]; then
    TEST_ID="s3-upload-$(date +%Y%m%d-%H%M%S)"
fi

# Get file info
FILE_NAME=$(basename "$FILE_PATH")
FILE_SIZE=$(stat -f%z "$FILE_PATH" 2>/dev/null || stat -c%s "$FILE_PATH")
FILE_SIZE_KB=$((FILE_SIZE / 1024))

# Main execution
print_header "TestForge S3 Upload Helper"

echo ""
print_info "Configuration:"
echo "  File:        $FILE_PATH"
echo "  File size:   ${FILE_SIZE_KB}KB"
echo "  S3 bucket:   $S3_BUCKET"
echo "  Expiration:  ${EXPIRATION_SECONDS}s ($(($EXPIRATION_SECONDS / 60)) minutes)"
echo "  Repository:  $GITHUB_REPO"
echo "  Test ID:     $TEST_ID"
echo ""

# Check dependencies
check_dependencies
echo ""

# Upload to S3
print_header "Step 1: Upload to S3"

S3_KEY="testforge/uploads/$(date +%Y-%m-%d)/${TEST_ID}/${FILE_NAME}"
S3_URI="s3://${S3_BUCKET}/${S3_KEY}"

print_info "Uploading to: $S3_URI"

if aws s3 cp "$FILE_PATH" "$S3_URI"; then
    print_success "File uploaded successfully"
else
    print_error "Failed to upload file to S3"
    exit 1
fi

echo ""

# Generate presigned URL
print_header "Step 2: Generate Presigned URL"

PRESIGNED_URL=$(aws s3 presign "$S3_URI" --expires-in "$EXPIRATION_SECONDS")

print_success "Presigned URL generated"
print_warning "URL expires in $(($EXPIRATION_SECONDS / 60)) minutes"
echo ""
echo "$PRESIGNED_URL"
echo ""

# Trigger workflow
print_header "Step 3: Trigger GitHub Actions Workflow"

print_info "Triggering workflow: action-2-combination-from-url.yml"

if gh workflow run action-2-combination-from-url.yml \
    -R "$GITHUB_REPO" \
    -f fileUrl="$PRESIGNED_URL" \
    -f testId="$TEST_ID"; then
    print_success "Workflow triggered successfully"
else
    print_error "Failed to trigger workflow"
    print_warning "You can manually trigger with:"
    echo ""
    echo "  gh workflow run action-2-combination-from-url.yml \\"
    echo "    -f fileUrl=\"$PRESIGNED_URL\" \\"
    echo "    -f testId=\"$TEST_ID\""
    exit 1
fi

echo ""

# Monitor workflow
print_header "Step 4: Monitor Workflow"

echo ""
print_info "To watch workflow progress:"
echo "  gh run watch -R $GITHUB_REPO"
echo ""
print_info "To list recent runs:"
echo "  gh run list -R $GITHUB_REPO --workflow=action-2-combination-from-url.yml"
echo ""
print_info "To download artifacts:"
echo "  gh run download -R $GITHUB_REPO"
echo ""

print_success "Done! Workflow is running."
print_info "Check progress at: https://github.com/$GITHUB_REPO/actions"
