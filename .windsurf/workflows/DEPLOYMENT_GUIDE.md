# PR Review Workflow - Deployment Guide

This guide explains how to deploy the PR Review workflow to other projects safely.

## Quick Start

### Single Project Deployment

```bash
# From the PR-Review project directory
python .windsurf/workflows/templates/deploy_workflow.py /path/to/target-project
```

### Multiple Projects Deployment

```bash
# Deploy to multiple projects at once
python .windsurf/workflows/templates/deploy_workflow.py \
  /path/to/affiliate-engine \
  /path/to/another-project \
  /path/to/third-project
```

### Using Windows Paths

```powershell
# PowerShell with Windows paths
python .windsurf/workflows/templates/deploy_workflow.py `
  "D:\projects\affiliate-engine" `
  "D:\projects\other-project"
```

## What Gets Deployed

The deployment script safely copies:

```
target-project/
└── .windsurf/
    └── workflows/
        ├── pr-review-comprehensive.md    # Main workflow file
        └── templates/                     # All Python helper scripts
            ├── jira_formatter.py
            ├── cli_formatter.py
            ├── generate-html.py
            ├── json_saver.py
            ├── database_uploader.py
            ├── api_impact_analyzer.py
            └── ... (all other templates)
```

## What It Does NOT Do

✅ **Safe Operations:**
- Does NOT delete any files
- Does NOT modify existing code
- Does NOT overwrite user files
- Does NOT remove `impact_analysis.py` or other project files
- Does NOT change working directory permanently

## Generated Output Directories

After running the workflow in a target project, generated files go to:

```
target-project/
└── .ai-review/              # Auto-created during workflow execution
    ├── pr-{pr_number}-data.json
    ├── pr-{pr_number}-data.html
    └── pr-{pr_number}-jira-comment.txt
```

**These are all gitignored** - they won't be committed to the repository.

## Pre-Deployment Checklist

Before deploying to a project, ensure:

- ✅ Target project directory exists
- ✅ Target project is a Git repository
- ✅ Target project has Bitbucket remote configured
- ✅ Python 3.8+ is installed
- ✅ Required dependencies: `jinja2`, `networkx` (optional: `pygraphviz`)

## Post-Deployment Setup

After deployment, configure each project:

### 1. Install Python Dependencies

```bash
cd /path/to/target-project
pip install jinja2 networkx
```

Optional (for dependency graphs):
```bash
pip install pygraphviz
```

### 2. Configure Environment Variables

```bash
# Linux/macOS
export ATLASSIAN_DOMAIN="your-instance.atlassian.net"
export ATLASSIAN_TOKEN="your_api_token"
export DB_HOST="localhost"
export DB_USER="root"
export DB_PASSWORD=""
export DB_NAME="pr_review_audit"

# Windows PowerShell
$env:ATLASSIAN_DOMAIN="your-instance.atlassian.net"
$env:ATLASSIAN_TOKEN="your_api_token"
```

### 3. Verify Deployment

```bash
cd /path/to/target-project

# List deployed files
ls -la .windsurf/workflows/

# Test workflow file integrity
cat .windsurf/workflows/pr-review-comprehensive.md | head -10
```

## Running the Workflow in Target Project

After deployment, you can run the workflow directly:

### From Windsurf IDE

1. Open target project in Windsurf
2. Checkout your feature branch
3. Open Workflow Panel
4. Select "PR Code Review - Comprehensive Analysis"
5. Click Run

### From Command Line

```bash
cd /path/to/target-project
python -m windsurf.workflows.pr_review_comprehensive --pr <pr_number>
```

## Troubleshooting

### "Workflow file not found"

```bash
# Verify deployment
ls .windsurf/workflows/pr-review-comprehensive.md

# If missing, re-deploy:
cd /path/to/PR-Review
python .windsurf/workflows/templates/deploy_workflow.py /path/to/target-project
```

### "Templates directory not found"

```bash
# Verify templates were copied
ls .windsurf/workflows/templates/*.py

# If missing, re-deploy (it's safe to re-run)
```

### "import jinja2" error

```bash
# Install dependencies
pip install jinja2 networkx
```

### Working Directory Issues

The deployment uses absolute paths, so working directory shouldn't matter:

```bash
# These all work the same way:
cd /path/to/target-project
python .windsurf/workflows/templates/jira_formatter.py .ai-review/pr-123-data.json

cd /
python /path/to/target-project/.windsurf/workflows/templates/jira_formatter.py /path/to/target-project/.ai-review/pr-123-data.json

# No file deletions or path corruption possible!
```

## Updating Deployment

When you update the workflow in the main PR-Review project:

```bash
# Re-run deployment (overwrites with latest)
python .windsurf/workflows/templates/deploy_workflow.py /path/to/target-project

# This safely updates all workflow files
# Your project files remain untouched
```

## Undeploying (Removing Workflow)

If you need to remove the workflow from a project:

```bash
# Simply delete the workflow directory (SAFE - no other files affected)
rm -rf /path/to/target-project/.windsurf/workflows
```

This only removes:
- The workflow markdown file
- The Python templates
- Any generated .ai-review files

**Does NOT affect:**
- Project source code
- Configuration files
- Other directories

## Multi-Project Workflow

Example workflow for managing PR Review across multiple projects:

```bash
#!/bin/bash

# Deploy to all projects
PROJECTS=(
  "/home/user/affiliate-engine"
  "/home/user/data-pipeline"
  "/home/user/api-gateway"
)

cd /home/user/PR-Review

for project in "${PROJECTS[@]}"; do
  echo "Deploying to $project..."
  python .windsurf/workflows/templates/deploy_workflow.py "$project"
done

echo "Deployment complete!"
```

## Security Notes

- ✅ Deployment script uses `shutil.copy2` (preserves file metadata)
- ✅ No shell execution or subprocess calls
- ✅ No file deletion (only copies)
- ✅ Path validation before operations
- ✅ Cross-platform compatible (Windows/Linux/macOS)

## Support

If you encounter issues:

1. Check deployment logs (run with default verbosity)
2. Verify paths are correct
3. Ensure target directory exists and is writable
4. Re-run deployment (it's idempotent - safe to run multiple times)
