# Git Advanced Reference

## Rebasing

### Interactive Rebase

```bash
# Rebase last N commits
git rebase -i HEAD~5

# Rebase onto branch
git rebase -i main

# Available commands:
# pick   = use commit
# reword = change commit message
# edit   = pause for amending
# squash = combine with previous
# fixup  = combine, discard message
# drop   = remove commit
```

### Example: Squash Commits

```bash
# Before
git log --oneline
# abc123 fix typo
# def456 add tests
# ghi789 implement feature

git rebase -i HEAD~3

# Editor shows:
pick ghi789 implement feature
squash def456 add tests
squash abc123 fix typo

# After
git log --oneline
# xyz999 implement feature
```

### Rebase vs Merge

```bash
# Merge: Creates merge commit, preserves history
git checkout main
git merge feature

# Rebase: Linear history, rewrites commits
git checkout feature
git rebase main
git checkout main
git merge feature  # Fast-forward

# Interactive rebase for cleanup before merge
git checkout feature
git rebase -i main
git checkout main
git merge --no-ff feature
```

## Cherry-Pick

```bash
# Pick a single commit
git cherry-pick abc123

# Pick multiple commits
git cherry-pick abc123 def456

# Pick range
git cherry-pick abc123..def456

# Cherry-pick without committing
git cherry-pick -n abc123

# Continue after conflict
git cherry-pick --continue

# Abort
git cherry-pick --abort
```

## Bisect

```bash
# Start bisect
git bisect start

# Mark current as bad
git bisect bad

# Mark known good commit
git bisect good v1.0.0

# Git checks out middle commit
# Test and mark
git bisect good  # or git bisect bad

# Repeat until found

# Reset when done
git bisect reset

# Automated bisect
git bisect start HEAD v1.0.0
git bisect run npm test
```

## Reflog

```bash
# View reflog
git reflog
git reflog show feature
git reflog --date=relative

# Recover deleted branch
git reflog | grep feature
git checkout -b feature abc123

# Recover from bad reset
git reflog
git reset --hard HEAD@{2}

# Recover lost commits
git reflog
git cherry-pick abc123
```

## Worktrees

```bash
# Create worktree
git worktree add ../hotfix hotfix-branch
git worktree add ../feature -b new-feature

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../hotfix

# Prune stale worktrees
git worktree prune
```

## Submodules

```bash
# Add submodule
git submodule add https://github.com/org/lib.git libs/lib

# Clone with submodules
git clone --recursive https://github.com/org/repo.git

# Initialize submodules (after clone)
git submodule update --init --recursive

# Update submodules
git submodule update --remote

# Remove submodule
git submodule deinit libs/lib
git rm libs/lib
rm -rf .git/modules/libs/lib
```

## Patches

```bash
# Create patch
git format-patch -1 HEAD
git format-patch main..feature

# Apply patch
git apply fix.patch
git am < fix.patch  # Apply as commit

# Create diff patch
git diff > changes.patch
git apply changes.patch
```

## Filter-branch / Filter-repo

```bash
# Remove file from entire history (use git-filter-repo)
pip install git-filter-repo
git filter-repo --path secrets.txt --invert-paths

# Change author
git filter-repo --commit-callback '
  if commit.author_email == b"old@email.com":
    commit.author_email = b"new@email.com"
'
```

## Hooks

```bash
# .git/hooks/pre-commit
#!/bin/sh
npm run lint || exit 1

# .git/hooks/commit-msg
#!/bin/sh
if ! grep -qE "^(feat|fix|docs|refactor|test|chore):" "$1"; then
  echo "Invalid commit message format"
  exit 1
fi

# Make executable
chmod +x .git/hooks/pre-commit
```

### Husky Setup

```bash
npm install husky lint-staged -D
npx husky install
npx husky add .husky/pre-commit "npx lint-staged"
```

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

## Advanced Log

```bash
# Find commits by content
git log -S "searchTerm"
git log -G "regex"

# Find commits by path
git log -- path/to/file

# Ancestry path
git log --ancestry-path main..feature

# First parent only
git log --first-parent

# Decoration
git log --decorate --graph

# Custom format
git log --format="%h %an %ar %s"
```

## Debugging

```bash
# Show file at specific commit
git show HEAD~3:path/to/file

# Find deleted file
git log --all --full-history -- "**/filename.*"

# Find when line was added
git log -S "code line" --source --all

# Verbose fetch
GIT_TRACE=1 git fetch

# Debug SSH
GIT_SSH_COMMAND="ssh -v" git fetch
```
