---
name: git-expert
description: Git expert with best practices. Use when working with Git, version control, branches, or needing Git workflow guidance.
---

# Git Expert

Expert in Git workflows, branching strategies, and version control best practices.

## When to Use This Skill

- Git operations and commands
- Branching strategy decisions
- Resolving merge conflicts
- Writing commit messages
- Code review workflows
- Git hooks and automation

## Branching Strategies

### Git Flow (Recommended for release-based projects)

```
main ─────●─────●─────●─────●─────●─────
          │     │     │     │
          │     └─────●─────●───●───●── (release/hotfix branches)
          │
develop ─●─────●─────●─────●─────●─────
          │     │
          │     └─●─●─●─ (feature branches)
          │
feature/user-story ─●───●───●──
```

```bash
# Main branches
main      # Production-ready, tagged releases
develop   # Integration branch for features

# Support branches
feature/*  # New features
release/*  # Release preparation
hotfix/*   # Emergency fixes
bugfix/*   # Bug fixes on develop
```

### Trunk-Based Development (Recommended for CI/CD)

```
main ───●───●───●───●───●───●───●───●───
        │   │   │   │   │   │   │   │
        └───┴───┴───┴───┴───┴───┴───┘
             short-lived branches
```

## Commit Conventions

### Conventional Commits

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance
- `perf`: Performance
- `ci`: CI/CD

**Examples:**
```
feat(auth): add OAuth2 login support

fix(trading): handle WebSocket reconnection on disconnect

docs(readme): update installation instructions

refactor(strategy): extract RSI calculation to utility

test(api): add unit tests for order execution
```

### Commit Message Rules

1. Subject line: 50 chars max, lowercase
2. Use imperative mood: "add" not "added"
3. No period at end
4. Body: 72 chars per line
5. Reference issues: "Closes #123"

## Essential Commands

### Basic Operations
```bash
# Stage and commit
git add -p                    # Stage hunks interactively
git add .                     # Stage all changes
git commit -m "message"       # Commit with message
git commit --amend            # Amend last commit
git commit --amend --no-edit  # Amend without changing message

# View history
git log --oneline -10         # Compact log
git log --graph --oneline     # Visual graph
git log -p file.txt           # File history with diffs
git blame file.txt            # Line-by-line blame

# Undo operations
git reset --soft HEAD~1       # Undo commit, keep changes staged
git reset HEAD file.txt       # Unstage file
git checkout -- file.txt      # Discard local changes
git restore file.txt           # Restore file (git 2.23+)
```

### Branching
```bash
# Create and switch
git checkout -b feature/new   # Create and switch
git switch -c feature/new     # Modern way

# List branches
git branch -a                 # All branches
git branch -vv                # With tracking info

# Delete branches
git branch -d feature/old      # Delete locally (merged)
git branch -D feature/old     # Force delete
git push origin --delete old  # Delete remote
```

### Merging and Rebasing
```bash
# Merge
git merge feature/new          # Merge into current
git merge --no-ff feature/new  # Preserve branch history

# Rebase (clean history)
git rebase main               # Rebase onto main
git rebase -i HEAD~5          # Interactive rebase

# Interactive rebase (squash, edit, reorder)
pick abc1234 First commit
squash def5678 Second commit
reword ghi9012 Fix message
```

### Remote Operations
```bash
# Fetch and pull
git fetch origin              # Fetch without merging
git pull --rebase origin main # Pull with rebase
git pull                      # Fetch and merge

# Push
git push origin main          # Push to remote
git push -u origin feature    # Set upstream
git push --force              # Force push (careful!)
git push --force-with-lease   # Safer force push
```

### Stashing
```bash
git stash                     # Stash changes
git stash push -m "message"   # Stash with message
git stash list                # List stashes
git stash pop                 # Apply and remove
git stash apply               # Apply without removing
git stash drop                # Delete stash
```

## Handling Conflicts

```bash
# Abort merge/rebase
git merge --abort
git rebase --abort

# Continue after resolving
git add resolved_file.txt
git rebase --continue

# Use theirs/ours
git checkout --theirs file.txt  # Use incoming
git checkout --ours file.txt   # Use current
```

### Visual Merge Tools
```bash
git config --global merge.tool vscode
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# Or use diff3 for better conflict view
git config merge.conflictstyle diff3
```

## Git Hooks

### Pre-commit Hook (.git/hooks/pre-commit)
```bash
#!/bin/sh
# Run linters and tests before commit

# Run linting
npm run lint || exit 1

# Run tests
npm test || exit 1

# Check formatting
npm run format-check || exit 1
```

### Commit Msg Hook (.git/hooks/commit-msg)
```bash
#!/bin/sh
# Validate commit message format

commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,50}"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "Invalid commit message format"
    echo "Expected: type(scope): description"
    exit 1
fi
```

### Install Hooks
```bash
# Make executable
chmod +x .git/hooks/pre-commit

# Or use husky (npm)
npm install husky --save-dev
npx husky install
npx husky add .husky/pre-commit "npm run lint"
```

## Git Workflows

### Feature Branch Workflow
```bash
# 1. Create feature branch
git checkout -b feature/add-login main

# 2. Work on feature
git add .
git commit -m "feat: add login form"

# 3. Keep up to date with main
git fetch origin
git rebase origin/main

# 4. Push and create PR
git push -u origin feature/add-login

# 5. After merge, clean up
git checkout main
git pull
git branch -d feature/add-login
```

### Code Review Workflow
```bash
# Create PR from branch
git push -u origin feature/my-feature

# Or use gh CLI (GitHub)
gh pr create --title "Add login" --body "Description"

# Review own changes before PR
git log main..HEAD
git diff main...HEAD

# Amend after review
git add .
git commit --amend
git push --force-with-lease
```

## Git Config

### Essential Settings
```bash
# Identity
git config --global user.name "Your Name"
git config --global user.email "email@example.com"

# Default branch
git config --global init.defaultBranch main

# Credentials
git config --global credential.helper store  # Or use keychain

# Merge strategy
git config --global pull.rebase false  # Merge on pull (default)

# Color
git config --global color.ui auto

# Aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
git config --global alias.last 'log -1 HEAD'
git config --global alias.unstage 'reset HEAD --'
```

## Best Practices

### Do's
- Commit early, commit often
- Write meaningful commit messages
- Keep commits atomic (one purpose)
- Use branches for features
- Review changes before committing (`git diff`)
- Sync with main regularly
- Use `.gitignore` for sensitive files

### Don'ts
- Don't commit secrets/keys
- Don't commit large binaries
- Don't force push to main/master
- Don't commit broken code
- Don't use `git push -f` on shared branches

### .gitignore Templates
```
# Dependencies
node_modules/
venv/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# IDEs
.idea/
.vscode/
*.swp

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
```

## Advanced Tips

### Search History
```bash
git log --author="John"              # By author
git log --since="2024-01-01"         # By date
git log --grep="fix"                 # By message
git log -S "function_name"           # Code search
git log --all --oneline --graph      # Full history
```

### Bisect (Find Bugs)
```bash
git bisect start
git bisect bad                   # Current is broken
git bisect good v1.0             # Known good commit
# Test each commit
git bisect good  # or bad
# After finding
git bisect reset
```

### Worktrees
```bash
# Work on multiple branches simultaneously
git worktree add ../feature-branch main
git worktree list
git worktree remove ../feature-branch
```

### Cherry Pick
```bash
# Apply specific commit to current branch
git cherry-pick abc1234
git cherry-pick -n abc1234  # No commit, just apply
```

## GitHub/GitLab CLI

```bash
# GitHub
gh pr create                    # Create PR
gh pr list                      # List PRs
gh pr checkout 123             # Checkout PR
gh issue create                 # Create issue

# GitLab
glab mr create                  # Create MR
glab issue list                 # List issues
```

## When Helping

- Ask about the team's workflow
- Check existing branch strategy
- Suggest aliases for frequently used commands
- Recommend hooks for quality control