---
status: accepted
---

# Make each request a stateless research run

Mars Research Assistant will optimize one request at a time: it acquires only the fields needed for the current question and returns Markdown plus an optional temporary standalone Board. It will not own a runtime, gateway, saved plan, cache, or cross-run history. This trades continuity and background orchestration for an install-and-use Skill whose behavior is easier to understand, verify, and distribute; temporary HTML or JSON exists only to deliver the current result.
