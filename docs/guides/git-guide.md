# Git Workflow Guide

This is a general-purpose Git workflow for personal projects. It assumes a hosted remote
such as GitHub, GitLab, or Azure Repos, but the local commands work with any Git host.
Examples use PowerShell; replace placeholder values such as `<branch-name>` with your own
names.

## The Basic Model

Think of Git work as three layers:

- **Working tree**: files you have changed but have not staged.
- **Staging area**: the exact changes that will enter the next commit.
- **Commit history**: permanent snapshots on your local branch.

A branch is a movable label pointing to a line of commits. A pull request proposes one
branch's commits for integration into another branch, usually `main` or `master`.

A useful default is:

```text
update main -> create task branch -> work and check -> commit -> push -> pull request
-> review and CI -> merge -> update main -> delete task branch
```

## Should I Use A Branch And Pull Request?

For personal projects, branches and pull requests are optional, but they are usually worth
using for anything meaningful. They provide a reviewable diff, a CI checkpoint, an explicit
place for discussion, and an easy rollback or comparison point. You can review your own PR;
the value is the record and the separation from `main`.

| Change | Suggested workflow |
| --- | --- |
| Feature, bug fix, refactor, migration, or documentation overhaul | Branch and PR |
| Several small changes with one purpose | One branch and PR |
| One-line typo or private experiment | Direct commit or short branch |
| Urgent fix | Short fix branch and expedited PR |
| Unrelated work found during a task | Separate branch or temporary stash |

Use one branch per **cohesive task**, not necessarily one branch per file or commit. Keep
unrelated cleanup out of the branch so the diff stays understandable.

## Start A New Task

First make sure you are starting from current `main`:

```powershell
git status --short
git switch main
git pull --ff-only origin main
git switch -c <type>/<short-description>
```

Common branch prefixes are:

```text
feat/add-search
fix/incorrect-total
docs/update-installation
refactor/split-client
chore/upgrade-dependencies
```

If your default branch has another name, use that instead of `main`. If your remote is not
called `origin`, check it with `git remote -v` and substitute its name.

## Work And Commit

Inspect changes before staging, stage only what belongs to the task, then inspect the staged
diff before committing:

```powershell
git status --short
git diff

# Stage everything for a simple focused task
git add -A

# Or stage selected files or hunks
git add path/to/file
# git add -p

git diff --cached
git commit -m "Describe the change"
```

A commit should be a coherent, working snapshot whenever practical. Several focused commits
are fine when they make the story clearer. Squashing before merge is also reasonable for a
small personal project. Never commit secrets, credentials, local databases, generated build
output, or files that should be ignored.

Run the project’s focused tests and checks before pushing. The exact commands belong to the
project, for example:

```powershell
# Replace these with the project's actual checks
<format-command>
<test-command>
<lint-command>
```

## Push And Open A Pull Request

The first push connects the local branch to the remote branch:

```powershell
git push --set-upstream origin <branch-name>
```

Open a pull request from `<branch-name>` into `main`. A useful PR should say what changed,
why it changed, how it was checked, and any known limitations. Keep the PR focused and let
CI finish before merging.

After the PR merges, return to a clean local `main`:

```powershell
git switch main
git pull --ff-only origin main
git branch -d <branch-name>
```

Delete the remote branch too if the hosting service does not do it automatically:

```powershell
git push origin --delete <branch-name>
```

## Keep A Branch Current

Fetch remote information without changing your files:

```powershell
git fetch origin
git log --oneline --decorate --graph HEAD..origin/main
```

For a private branch, rebasing gives a linear history:

```powershell
git rebase origin/main
git push --force-with-lease
```

Use `--force-with-lease`, never plain `--force`, when rewriting a branch that has already
been pushed. If other people use the branch, merge instead:

```powershell
git merge origin/main
```

Resolve conflicts, stage the resolved files, and continue:

```powershell
git add <resolved-file>
git rebase --continue
# Or, during a merge:
git commit
```

To abandon an in-progress operation:

```powershell
git rebase --abort
# Or:
git merge --abort
```

## Recover Uncommitted Work

### You Are On The Wrong Branch

If the changes are uncommitted, stash them, move to the correct base, create the task
branch, and restore them:

```powershell
git status --short
git diff
git stash push --include-untracked -m "WIP task description"

git fetch origin
git switch main
git pull --ff-only origin main
git switch -c <correct-branch>
git stash pop
```

`--include-untracked` matters when the work includes new files. If `stash pop` reports a
conflict, resolve it normally. Check whether the stash remains before deleting anything:

```powershell
git stash list
git status --short
```

If you have only a few changes, another option is to create the new branch directly from
your current branch. The uncommitted files come with you:

```powershell
git switch -c <correct-branch>
```

Use this shortcut only when the current branch already points at the right base.

### You Need To Pause Work

Stash work when you need a clean tree for another task or branch switch:

```powershell
git stash push --include-untracked -m "WIP description"
git stash list
git stash pop
```

A temporary WIP commit on a private branch is often easier to understand and recover than a
large collection of stashes. You can clean it up later with an interactive rebase before
opening the PR.

## Recover Committed Work

### Commits Are On The Wrong Local Branch

If the commits are not pushed, create the correct branch at the current commit, then reset
the old branch back to its intended base:

```powershell
# While on the branch containing the commits
git switch -c <correct-branch>

# Move the old branch back, after confirming the commit IDs
git switch <old-branch>
git log --oneline -n 5
git reset --hard origin/main
```

`reset --hard` discards uncommitted changes on the branch, so confirm `git status` is clean
and verify the commits are safely present on `<correct-branch>` first.

If you want to move selected commits instead, use `cherry-pick`:

```powershell
git switch <correct-branch>
git cherry-pick <commit-sha>
```

For commits already pushed to a shared branch, avoid rewriting history. Create a new branch
from the correct base and cherry-pick the needed commits, or revert the original commits and
make a clean follow-up PR.

### Work Was Committed After The PR Already Merged

A merged PR cannot be separated retroactively by renaming a branch. The commits are already
part of the target branch's history. Treat any remaining work as a new task:

```powershell
git switch main
git pull --ff-only origin main
git switch -c <follow-up-branch>
```

## Undo Changes Safely

Choose the undo command based on where the change exists:

| Situation | Command | Effect |
| --- | --- | --- |
| Unstaged file changes | `git restore <file>` | Discards working-tree changes |
| Staged changes | `git restore --staged <file>` | Unstages; keeps file changes |
| A local commit not pushed | `git reset --soft HEAD~1` | Removes commit; keeps changes staged |
| A local commit not pushed | `git reset HEAD~1` | Removes commit; keeps changes unstaged |
| A pushed/shared commit | `git revert <commit-sha>` | Creates a new undo commit |

Avoid `reset --hard` unless you have confirmed the work is disposable or backed up. When in
doubt, create a safety branch or stash first:

```powershell
git branch backup-before-recovery
git stash push --include-untracked -m "backup before recovery"
```

## Useful Inspection Commands

```powershell
git status
git log --oneline --decorate --graph --all -n 20
git diff
git diff --cached
git show <commit-sha>
git branch --all --verbose
git remote -v
git reflog
```

`git reflog` can often recover a commit or branch tip after an accidental reset or rebase.
It is local recovery history, so use it before assuming work is lost.

## Practical Rules

- Keep the default branch buildable and easy to run.
- Start meaningful work from an up-to-date default branch.
- Use short-lived branches with names that describe the task.
- Keep one PR focused on one coherent outcome.
- Review both `git diff` and `git diff --cached`.
- Run the project’s checks before and during review.
- Prefer `revert` for shared history and reserve rewriting for private branches.
- Use `--force-with-lease` when a pushed private branch must be rewritten.
- Keep backups before destructive recovery commands.
- Delete merged branches so active work is easy to see.
