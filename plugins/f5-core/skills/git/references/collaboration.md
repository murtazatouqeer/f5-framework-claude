# Git Collaboration Reference

## Pull Requests

### Creating a PR

```bash
# Create feature branch
git checkout main
git pull
git checkout -b feature/new-feature

# Make changes
git add .
git commit -m "feat: add new feature"

# Push branch
git push -u origin feature/new-feature

# Create PR via CLI (GitHub)
gh pr create --title "Add new feature" --body "Description"

# Create PR with template
gh pr create --template PULL_REQUEST_TEMPLATE.md
```

### Reviewing PRs

```bash
# Fetch PR locally
gh pr checkout 123

# View PR diff
gh pr diff 123

# Review comments
gh pr review 123 --approve
gh pr review 123 --request-changes --body "Please fix X"
gh pr review 123 --comment --body "Looks good!"
```

### Updating PR

```bash
# Fetch latest from main
git checkout feature/new-feature
git fetch origin main
git rebase origin/main

# Force push after rebase
git push --force-with-lease

# Squash commits before merge
git rebase -i main
# Mark all but first as 'squash'
git push --force-with-lease
```

## Merge Conflicts

### Resolving Conflicts

```bash
# During merge
git merge feature
# CONFLICT in file.txt

# View conflict markers
<<<<<<< HEAD
current branch content
=======
incoming branch content
>>>>>>> feature

# Resolve and continue
git add file.txt
git merge --continue

# Abort merge
git merge --abort
```

### During Rebase

```bash
git rebase main
# CONFLICT in file.txt

# Resolve conflict
git add file.txt
git rebase --continue

# Skip commit
git rebase --skip

# Abort rebase
git rebase --abort
```

### Using Mergetool

```bash
# Configure tool
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# Use tool
git mergetool

# Accept theirs/ours
git checkout --theirs file.txt
git checkout --ours file.txt
```

## Code Review

### Best Practices

```markdown
## Reviewer Checklist
- [ ] Code is readable and well-organized
- [ ] Logic is correct and efficient
- [ ] Edge cases are handled
- [ ] Tests cover the changes
- [ ] No security vulnerabilities
- [ ] Documentation is updated
- [ ] Commit messages are clear
```

### Review Comments

```markdown
# Constructive feedback patterns

## Suggestion
"Consider using `map()` here for better readability"

## Question
"What happens if this value is null?"

## Nitpick
"nit: extra whitespace"

## Blocking
"This introduces a SQL injection vulnerability. Please use parameterized queries."

## Praise
"Nice refactoring! This is much cleaner."
```

## Remote Management

### Multiple Remotes

```bash
# List remotes
git remote -v

# Add remote
git remote add upstream https://github.com/original/repo.git

# Rename remote
git remote rename origin github

# Remove remote
git remote remove upstream

# Change remote URL
git remote set-url origin git@github.com:user/repo.git
```

### Syncing Forks

```bash
# Add upstream
git remote add upstream https://github.com/original/repo.git

# Fetch upstream
git fetch upstream

# Merge upstream changes
git checkout main
git merge upstream/main
git push origin main

# Rebase feature branch
git checkout feature
git rebase upstream/main
```

## Team Practices

### Branch Protection

```yaml
# GitHub branch protection settings
branches:
  main:
    protection:
      required_status_checks:
        strict: true
        contexts:
          - ci/build
          - ci/test
      required_pull_request_reviews:
        required_approving_review_count: 1
        dismiss_stale_reviews: true
      enforce_admins: true
      restrictions:
        users: []
        teams: []
```

### CODEOWNERS

```
# .github/CODEOWNERS
* @default-reviewers
/frontend/ @frontend-team
/backend/ @backend-team
/docs/ @tech-writers
*.sql @database-team
```

### Signing Commits

```bash
# Generate GPG key
gpg --full-generate-key

# Get key ID
gpg --list-secret-keys --keyid-format=long

# Configure Git
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Sign commit
git commit -S -m "Signed commit"

# Verify signature
git log --show-signature
```

## Collaborative Commands

```bash
# View who changed what
git blame file.txt
git log --follow -p -- file.txt

# Find contributors
git shortlog -sn

# View branch authors
git for-each-ref --sort=-committerdate refs/heads/ \
  --format='%(committerdate:short) %(authorname) %(refname:short)'

# Show all contributors to a file
git log --format='%an' -- file.txt | sort | uniq -c | sort -rn
```

## Handling Large Files

### Git LFS

```bash
# Install LFS
git lfs install

# Track file types
git lfs track "*.psd"
git lfs track "*.zip"

# View tracked patterns
cat .gitattributes

# View LFS files
git lfs ls-files

# Migrate existing files
git lfs migrate import --include="*.psd"
```
