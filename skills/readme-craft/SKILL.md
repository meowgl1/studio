---
name: readme-craft
description: Create, edit, audit, or improve a README.md following professional best practices — structure, badges, visuals, tone, and completeness. Use this skill whenever the user wants to work on a README, write a new one, update an existing one, improve its quality, add badges or icons, translate it, or audit it for missing sections. Trigger even if the user just says "lavoriamo sul readme" or "update the readme" or "il readme è da migliorare".
---

# Skill — README Craft

Treat a README as part of the product, not an afterthought. It is the first thing a collaborator, recruiter, or user sees. A great README answers three questions before the reader asks them: **What is this? How do I use it? Why should I care?**

---

## Workflow

### 1. Audit first

Before writing anything, read the existing README (if one exists) and check for:

- Missing sections (see canonical structure below)
- Outdated information (setup steps, badge links, version numbers)
- Walls of text with no visual structure
- Missing visuals (demo, screenshots, GIF)
- No badges or stale badges
- Tone mismatches (too casual, too corporate, too jargon-heavy)

Report findings to the user as a short punch list before touching anything.

### 2. Identify the audience

Ask (or infer from the repo) who the primary reader is:

- **Contributors** → emphasize setup, architecture, contribution guide
- **End users** → emphasize installation, usage, features
- **Recruiters / evaluators** → emphasize what problem it solves, tech stack, demo
- **Mixed** → lead with user-facing content, link to contributor docs

### 3. Apply the canonical structure

Use this order. Omit sections that genuinely don't apply — never add placeholder sections.

```
1. Title + tagline         ← clear identifier + one-line pitch
2. Badges                  ← build, license, version, language
3. Demo / Screenshot       ← GIF or image showing it in action
4. Description             ← plain English, 3–5 sentences max
5. Features                ← bullet list of key capabilities
6. Tech Stack              ← languages, frameworks, major deps
7. Installation            ← step-by-step, copy-paste ready
8. Usage                   ← how to run + examples
9. Configuration           ← env vars, config files (if applicable)
10. Contributing           ← PR process, coding standards link
11. License                ← one line + badge
12. Credits / Acknowledgments ← optional, but classy when relevant
```

### 4. Write or rewrite

Apply these rules:

- **Active, direct language.** "Runs X" not "X can be run."
- **No jargon for newcomers** unless the audience is clearly expert.
- **Limit line length** to 80–100 characters in prose paragraphs.
- **Consistent heading hierarchy** — never skip levels (h2 → h4 is wrong).
- **White space is content** — separate sections, break up bullet lists.
- **Code blocks for all commands** — never inline `bash commands` in prose.
- **Emojis sparingly** — section headers only, max one per section, only if the project's tone supports it.

### 5. Validate before finishing

- All links resolve (no dead anchors or broken URLs)
- Code snippets are copy-paste ready and tested
- Badges use correct repo/org slug
- Installation flow tested on a clean environment (or flagged as untested)

---

## Badges

Generate badges via **[Shields.io](https://shields.io)**. Common patterns:

```markdown
<!-- Build status (GitHub Actions) -->
![CI](https://github.com/ORG/REPO/actions/workflows/ci.yml/badge.svg)

<!-- License -->
![License](https://img.shields.io/github/license/ORG/REPO)

<!-- Latest release -->
![Release](https://img.shields.io/github/v/release/ORG/REPO)

<!-- Language -->
![Python](https://img.shields.io/badge/python-3.11+-blue)

<!-- Stars -->
![Stars](https://img.shields.io/github/stars/ORG/REPO?style=social)

<!-- Last commit -->
![Last Commit](https://img.shields.io/github/last-commit/ORG/REPO)

<!-- Coverage (Codecov) -->
![Coverage](https://codecov.io/gh/ORG/REPO/branch/main/graph/badge.svg)
```

Badge style options: `flat` (default), `flat-square`, `for-the-badge`, `plastic`.  
Use `for-the-badge` only for prominent single badges (e.g., license). Stick to one style throughout.

---

## Icons and Visuals

### Tech stack icons

Use **[Devicons](https://devicons.github.io/devicon/)** or **[Simple Icons](https://simpleicons.org)** via shields.io for inline tech logos:

```markdown
<!-- Via shields.io + simpleicons -->
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?logo=nextdotjs&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
```

For a full tech stack row, align them in one paragraph (no list, no table):

```markdown
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
```

### Screenshots and GIFs

```markdown
<!-- Full-width screenshot -->
![App screenshot](docs/assets/screenshot.png)

<!-- Centered with caption -->
<p align="center">
  <img src="docs/assets/demo.gif" width="700" alt="Demo">
</p>
```

- Prefer GIFs for CLI tools and interactive UIs — they show the product in motion
- Host assets in `docs/assets/` or `.github/assets/` — never a third-party image host
- Keep GIFs under 5MB; use [ezgif.com](https://ezgif.com) to compress

---

## Multi-language READMEs

When the project supports multiple locales:

```markdown
<!-- At the top of each README, before any other content -->
🌍 [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)
```

- `README.md` is always the English (primary) version
- Translated files: `README.it.md`, `README.es.md`, `README.zh.md`, etc.
- Keep translations in sync — flag stale translations with a banner:

```markdown
> ⚠️ This translation may be outdated. The [English version](README.md) is authoritative.
```

---

## Tools

| Tool | Purpose | URL |
|------|---------|-----|
| Shields.io | Badge generator — build, version, license, custom | https://shields.io |
| Simple Icons | SVG brand icons for 3000+ tech tools | https://simpleicons.org |
| Devicon | Tech-specific colored icons | https://devicons.github.io/devicon/ |
| readme.so | Drag-and-drop README section builder | https://readme.so |
| StackEdit | Browser-based markdown editor with live preview | https://stackedit.io |
| Dillinger | Lightweight online markdown editor | https://dillinger.io |
| ezgif.com | GIF optimization and conversion | https://ezgif.com |
| carbon.now.sh | Beautiful code screenshot images | https://carbon.now.sh |

---

## Examples

### Example 1 — Minimal open source CLI tool

```markdown
# toolname

> One-line description of what it does.

![License](https://img.shields.io/github/license/user/toolname)
![Release](https://img.shields.io/github/v/release/user/toolname)

## Installation

\`\`\`bash
pip install toolname
\`\`\`

## Usage

\`\`\`bash
toolname --input file.csv --output result.json
\`\`\`

## License

MIT
```

### Example 2 — Full-featured web app README

```markdown
# AppName

> Tagline — what it does in one sentence.

![CI](https://github.com/org/repo/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/github/license/org/repo)

<p align="center">
  <img src="docs/assets/demo.gif" width="700" alt="Demo">
</p>

## Description

Plain English, 3–5 sentences. No jargon. Explain the problem it solves
and who it is for.

## Features

- Feature one — brief explanation
- Feature two
- Feature three

## Stack

![Next.js](https://img.shields.io/badge/Next.js-000?logo=nextdotjs&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)

## Installation

\`\`\`bash
git clone https://github.com/org/repo
cd repo
cp .env.example .env   # fill in required values
npm install
npm run dev
\`\`\`

## Contributing

Open an issue first. PRs welcome after discussion.

## License

MIT
```

### Example 3 — Internal tool / context system (like .studio)

Lead with **what it is** (not what it contains), then **how it works**, then structure, then setup. Internal tools often have a "personal opinion" or "why I built this" section — this is appropriate and humanizes the project for evaluators and collaborators.

---

## Common mistakes to avoid

- Omitting the project description entirely
- Starting with installation before explaining what the project is
- Using `git clone` without specifying the full repo URL
- Including `.env` values with real credentials in examples
- Badges that point to a different repo (broken after fork/rename)
- Sections that exist but say "coming soon" or "TODO" — remove them
- Overusing bold, italics, and `code` formatting until emphasis is meaningless
- Long walls of text with no visual breaks
- A README that is just a copy of the API documentation

---

## Checklist before done

- [ ] Title and tagline are clear and distinct
- [ ] At least one visual (screenshot, GIF, or diagram) if the project has a UI
- [ ] Badges are correct and resolve to the right repo
- [ ] Installation steps are copy-paste ready
- [ ] Usage includes at least one real example
- [ ] No dead links
- [ ] No placeholder sections ("Coming soon", "TODO")
- [ ] Tone is consistent throughout
- [ ] Line length is comfortable to read (≤ 100 chars)
- [ ] Multi-language banner at the top (if project has translated READMEs)
