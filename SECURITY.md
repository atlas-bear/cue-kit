# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes       |
| < 0.3   | No        |

Security fixes are released as a new patch version and noted in [CHANGELOG.md](CHANGELOG.md).

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report privately through GitHub: go to the repository's **Security** tab and choose
**Report a vulnerability** ([direct link](https://github.com/atlas-bear/cue-kit/security/advisories/new)).
Include the affected version, steps to reproduce, and the impact you observed.

AB//LABS aims to acknowledge reports within 3 business days and to share a remediation
plan or fix timeline within 10 business days.

## Scope notes

- cue-kit runs `yt-dlp`, `ffmpeg`, and `ffprobe` as subprocesses with argument lists
  (never through a shell). Vulnerabilities in those tools should be reported upstream.
- API keys are read from the environment or local `.env` files and are sent only to the
  selected Whisper provider (Groq or OpenAI) over HTTPS.
- See the README's "Data handling" section for exactly what data leaves the machine.
