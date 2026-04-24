# GitHub Cutover Runbook

This runbook implements the repository identity cutover from:

- `byteworthy/Hafz-Defend`

To:

- `ByteWorthyLLC/byteworthy-defend`

## Preconditions

- You have `admin` permissions on source repo and target organization.
- `gh` CLI is authenticated with required scopes.
- Target name `byteworthy-defend` is available in `ByteWorthyLLC`.

## Cutover Steps

1. Transfer repository:
   - GitHub UI: Settings -> Danger Zone -> Transfer Ownership
   - New owner: `ByteWorthyLLC`
   - Keep repository name temporarily if needed for staged rename.
2. Rename repository to `byteworthy-defend`.
3. Set default branch to `main`.
4. Verify redirect from old path still resolves.
5. Confirm issues, PRs, releases, and commit history are intact.
6. Apply repository metadata:
   - description
   - homepage
   - topics
7. Ensure org-standard health files exist and are active.

## Post-Cutover Validation

- `git clone` from new URL works.
- old URL redirects to new URL.
- branch protection is present on `main`.
- required checks are configured.

## Local Remote Update

```bash
git remote set-url origin git@github.com:ByteWorthyLLC/byteworthy-defend.git
```
