# Mars Research Assistant Agent Rules

## Remote publication approval gate

All project changes are local-only by default. Without the user's explicit
approval for the exact action and target, no Agent may:

- push commits or branches to any remote;
- create, update, reopen, close, or merge a pull request that publishes project
  changes;
- create or move a tag, publish a GitHub Release, or publish a package;
- deploy or otherwise synchronize project changes to any online environment.

Local editing, tests, builds, reviews, and commits are allowed when they are
within the assigned task. Before requesting approval for an online action, the
Agent must report the relevant local diff or commit, tests run and their
results, the exact remote target, and the proposed action.

A general instruction to finish a task, a prior approval for another action,
or approval to work locally is not permission to publish online. Approval must
be obtained separately for each concrete remote publication step.

## Version approval gate

The user exclusively decides when to assign or change a version. Until the user
explicitly names the target version after reviewing the project to their
satisfaction, no Agent may:

- change a version field in project metadata, manifests, documentation, or
  generated artifacts;
- describe unreleased work as a released version;
- create, move, or push a version tag;
- create, edit, publish, or announce a Release.

Issue titles, roadmaps, prior conversation, or an earlier tentative release
target do not count as approval to set a version. Version changes and release
publication are separate approval gates and each requires a fresh, explicit
instruction from the user.

## Master integration gate

Every change merged into `master` must belong to a versioned change set whose
version number was explicitly assigned by the user. Work that has not yet been
assigned a version must first be combined and validated on a temporary
integration branch; it may not be merged directly into `master`.

Creating or updating a temporary integration branch does not authorize a
version change, remote push, pull request, merge, tag, release, package
publication, or deployment. Those actions remain subject to the separate
approval gates above.
