# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security vulnerabilities. Report privately so maintainers can
assess and fix the issue before disclosure.

- **GitCode (primary):** https://gitcode.com/grape-dev/grape-template/issues
  - choose the "private / security" report option
- **Email:** `jansonzhe@gmail.com`

Please include:

- Environment / platform version
- Steps to reproduce (or a minimal repro project)
- Impact description (what could be accessed or exploited)
- Any logs, screenshots, or error output

## What is covered

- Malicious or obfuscated scripts inside a template (dependency confusion, credential theft, data exfiltration)
- Registry content that would mislead template consumers (wrong `source_repo`, masked URLs, invalid scenes)
- Committed secrets, internal endpoints, or personal data in this repository's history

## Response expectations

- **Acknowledgment** within 3 business days.
- We will inform you about next steps and expected timelines; security fixes land as soon as a patch is ready and are released together with the affected template update.

## Safe harbor

We commit to not pursuing legal action against security researchers who act in good faith and follow this policy.