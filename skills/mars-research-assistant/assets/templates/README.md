# Blank Public Templates

These templates define empty schemas and prompts for a user-owned private
runtime. They contain no default watchlist, portfolio, setup, trading profile,
personal risk parameter, broker state, or research history.

Each user initializes a private runtime locally. Skill installation and upgrade
must never restore or overwrite user state from this directory.

| Format | Public contract |
| --- | --- |
| CSV | Header-only schemas with no user rows. |
| Markdown/TOML | Blank scaffolding to be initialized and owned on the user's device. |
