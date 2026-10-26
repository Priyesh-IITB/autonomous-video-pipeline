# Sources: CVE-2026-82533 video (fact-checked 2026-10-21)

- dsh repo, README, sandbox modes, SAFETY.md: https://github.com/deepseek-ai/deepseek-harness (docs/subsystems/sandbox.md, SAFETY.md)
- The Hacker News, Sep 9 2026: https://thehackernews.com/2026/09/deepseek-harness-flaw-let-ai-agents.html
- VulnCheck advisory: https://www.vulncheck.com/advisories/deepseek-harness-alpha-1-authentication-bypass-via-host-header-spoofing
- GitHub advisory: https://github.com/advisories/GHSA-8m2g-8cgm-3vcp
- NVD (CVSS 4.0 9.4 / 3.1 9.6, both VulnCheck): https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=CVE-2026-82533
- Forkast (log attributed to user, OX test): https://forkast.news/deepseek-harness-sandbox-escape-lets-ai-agents-disable-their-own-confinement/
- Yahoo Tech (bubblewrap shares host network ns; no in-the-wild exploitation): https://tech.yahoo.com/cybersecurity/articles/deepseek-harness-sandbox-escape-lets-193950399.html
- Discussion #250 (Aug 13): https://github.com/deepseek-ai/deepseek-harness/discussions/250
- Fix commit 3e24087: https://github.com/deepseek-ai/deepseek-harness/commit/3e24087bfaeabe40b58ba2f7b936895b8f93fe27
- Release dsh-v0.1.2-alpha.1: https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.1.2-alpha.1
- npm registry (0.1.2-alpha.2 on Aug 30): https://registry.npmjs.org/@deepseek-ai/dsh
- Neomanex (transcripts possibly exposed if reachable): https://neomanex.com/news/deepseek-harness-cve-2026-82533-sandbox-escape

Deliberately NOT claimed (unverified): delivery via a repo file, the default mode name, any OX or
DeepSeek quote, OX's discovery date, "first confirmed instance".
