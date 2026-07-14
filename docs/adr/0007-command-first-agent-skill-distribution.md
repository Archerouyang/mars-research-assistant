# Use an Agent Skill as the primary distribution form

Trading Research System is distributed primarily as one self-contained Agent
Skill installed through `npx skills`, while Codex and Claude plugins are
optional managed wrappers around the same public behavior. This keeps the core
workflow portable across coding agents and avoids making an official plugin
directory or one vendor's manifest the product boundary; private runtime state
remains outside every package.
