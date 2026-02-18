#!/bin/bash

# PR Review Workflow - Easy Deployment Script
# Usage: ./deploy.sh /path/to/project1 /path/to/project2 ...

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if projects provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ No projects specified${NC}"
    echo "Usage: $0 /path/to/project1 /path/to/project2 ..."
    echo ""
    echo "Example:"
    echo "  $0 ~/affiliate-engine ~/data-pipeline ~/api-gateway"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}PR Review Workflow Deployment${NC}"
echo "=============================="
echo ""
echo "Source: $SCRIPT_DIR"
echo "Target projects: $#"
echo ""

# Deploy to each project
SUCCESSFUL=0
FAILED=0

for PROJECT in "$@"; do
    # Resolve to absolute path
    PROJECT=$(cd "$PROJECT" 2>/dev/null && pwd || echo "$PROJECT")

    if [ ! -d "$PROJECT" ]; then
        echo -e "${RED}❌ Directory not found: $PROJECT${NC}"
        ((FAILED++))
        continue
    fi

    echo -e "${YELLOW}→ Deploying to: $PROJECT${NC}"

    # Create directories
    mkdir -p "$PROJECT/.windsurf/workflows/templates"

    # Copy workflow file
    cp "$SCRIPT_DIR/pr-review-comprehensive.md" "$PROJECT/.windsurf/workflows/"

    # Copy all template files
    cp "$SCRIPT_DIR/templates"/*.py "$PROJECT/.windsurf/workflows/templates/" 2>/dev/null || true

    # Create/update .gitignore
    if [ -f "$PROJECT/.gitignore" ]; then
        grep -q ".ai-review" "$PROJECT/.gitignore" || echo ".ai-review/" >> "$PROJECT/.gitignore"
    else
        echo ".ai-review/" > "$PROJECT/.gitignore"
    fi

    echo -e "${GREEN}✅ Deployed to: $(basename $PROJECT)${NC}"
    ((SUCCESSFUL++))
done

echo ""
echo "=============================="
echo -e "${GREEN}✅ Deployment Summary${NC}"
echo "Successful: $SUCCESSFUL"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All deployments completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some deployments failed${NC}"
    exit 1
fi
