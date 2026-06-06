# .studio

> Un sistema di gestione del contesto AI-agnostico per progetti software.

🌍 [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)

---

## 🧠 Cos'è

`.studio` è una cartella strutturata di file markdown che fornisce a qualsiasi assistente AI — Claude Code, Gemini CLI, Cursor, o qualsiasi altro — una comprensione coerente e stratificata del tuo modo di lavorare, prima ancora che scriva una singola riga di codice.

Non è un plugin. Non è un framework. È un insieme di file.

---

## 🙏 Riconoscimenti

L'espansione v2.0 di questo sistema si è ispirata a **[ECC](https://github.com/affaan-m/ECC)** di [@affaan-m](https://github.com/affaan-m), vincitore del Claude hackathon. ECC ha dimostrato come appare un sistema AI di contesto pienamente operativo alla scala — 97 agenti, 300+ skills, 20+ hook, supporto cross-tool su 7 piattaforme AI.

Questo progetto ha preso una direzione diversa: invece di un sistema CLI-pesante, `.studio` adatta i pattern più preziosi di ECC in un layer leggero, Python-nativo e AI-agnostico. L'architettura delle regole, i contesti, l'infrastruttura degli hook e il design degli agenti sono stati tutti modellati studiando l'approccio di ECC.

---

## ⚙️ Come funziona

Ogni sessione AI in un progetto inizia con una cascata:

```
project/CLAUDE.md (o GEMINI.md, .cursorrules, ecc.)
  └── @.studio/STUDIO.md              ← contesto di progetto
        └── @~/.studio/STUDIO.md      ← standard globali
              ├── harness.md           ← regole di engineering
              ├── stack.md             ← decisioni tecnologiche
              ├── persona.md           ← stile di comunicazione
              ├── IGNORE.md            ← file da non toccare mai
              ├── evals.md             ← metriche di successo agenti
              ├── rules/               ← regole per linguaggio
              ├── contexts/            ← comportamento per modalità
              ├── skills/              ← procedure riutilizzabili
              └── agents/              ← subagenti specializzati
```

Il tool AI legge il file di ingresso, che espande tutti i riferimenti `@` in sequenza. Quando il modello legge il tuo primo messaggio, conosce già i tuoi standard di engineering, lo stack tecnologico, le regole attive e come preferisci comunicare.

Il `~/.studio/` globale si applica a ogni progetto sulla tua macchina. Il `.studio/` di ogni progetto eredita dal globale e aggiunge il proprio contesto — architettura, sprint corrente, trappole note.

---

## 🗂️ Struttura

### Globale (`~/.studio/`)

#### 📌 Standard

| File | Scopo |
|------|-------|
| `STUDIO.md` | Punto di ingresso. Referenzia tutti i file globali. Definisce il protocollo di sessione, i punti di estensione, gli agenti e le skills disponibili. |
| `harness.md` | Cinque assoluti di engineering: schema-first, evals-driven, context engineering, failure-aware, observability. |
| `stack.md` | Decisioni tecnologiche — definitive, non suggerimenti. Python, TypeScript, Next.js, Supabase. Niente LangChain. |
| `persona.md` | Contratto comunicativo. Diretto, code-first, niente convenevoli, italiano o inglese per sessione. |
| `IGNORE.md` | File che l'AI non deve mai modificare: `.env*`, `.git/`, build artifacts, migrations. |
| `evals.md` | Come sapere se gli agenti stanno avendo successo. Regole di logging di sessione. |

#### 📏 Regole (`rules/`)

Standard di codice applicabili, caricati ogni sessione. Organizzati per scope:

| Cartella | Contenuto |
|----------|-----------|
| `rules/common/` | `clean-code` · `clean-architecture` · `testing` · `performance` · `patterns` · `security` · `llm-security` · `git` · `hooks` |
| `rules/python/` | `coding-style` · `patterns` · `testing` · `security` · `fastapi` |
| `rules/js/` | `coding-style` · `patterns` · `testing` · `security` · `react` |
| `rules/sql/` | `coding-style` · `patterns` · `security` |

#### 🎭 Contesti (`contexts/`)

File di comportamento per modalità. Carica quello che corrisponde alla tua attività corrente:

| File | Quando usarlo |
|------|---------------|
| `contexts/dev.md` | Stai attivamente costruendo o correggendo codice |
| `contexts/research.md` | Stai investigando una codebase o un problema |
| `contexts/review.md` | Stai revisionando una PR o facendo un audit del codice |

Ogni file di contesto attiva le regole rilevanti e definisce il comportamento appropriato per quella modalità.

#### 🛠️ Skills (`skills/`)

Procedure riutilizzabili invocate per nome durante le sessioni:

| Skill | Scopo |
|-------|-------|
| `spec-driven-development` | Workflow spec-first — obbligatorio prima di qualsiasi nuova feature |
| `webapp-testing` | Setup e pattern di testing E2E con Playwright |
| `backend-patterns` | API design, service layer, repository, auth, caching |
| `frontend-patterns` | Next.js App Router, Server Components, data fetching |
| `docker-patterns` | Build multi-stage, Compose per dev locale, hardening security |
| `api-design` | Convenzioni REST, formato risposta, paginazione, versioning |
| `coding-standards` | Setup linting, pre-commit hooks, CI enforcement |
| `git-workflow` | Strategia di branching, disciplina sui commit, processo PR |
| `security-review` | Checklist OWASP — da eseguire prima di fare merge di codice auth/payment |
| `eval-harness` | Costruire harness di valutazione per feature AI/LLM |
| `tracker` | Logging costi sessione e token |
| `caveman` | Pattern di scripting minimali, senza dipendenze |
| `multi-agent-patterns` | Quando e come spawnare subagenti — template di handoff, regole per il lavoro in parallelo, anti-pattern |

#### 🤖 Agenti (`agents/`)

Subagenti specializzati invocati per nome. Ognuno ha un ruolo definito e un formato di output:

| Agente | Scopo |
|--------|-------|
| `architect` | System design, ADR, analisi trade-off, pianificazione scalabilità |
| `planner` | Scomporre i requisiti in piani di implementazione per fasi |
| `tdd-guide` | Enforcement test-first — scrive i test prima dell'implementazione |
| `performance-optimizer` | Trovare e correggere query N+1, endpoint lenti, bundle bloat |
| `security-reviewer` | Risposta a incidenti di sicurezza e audit approfonditi |
| `refactor-cleaner` | Migliorare la struttura senza cambiare il comportamento |
| `code-explorer` | Mappare codebase non familiari — entry point, pattern, trappole |
| `code-simplifier` | Rimuovere astrazioni premature e complessità non necessaria |
| `doc-updater` | Mantenere context.md, gotchas.md e README in sync con il codice |

#### 🪝 Hook (`hooks/`, `scripts/`)

Automazione che si esegue intorno alle sessioni AI:

| Hook | Trigger | Cosa fa |
|------|---------|---------|
| `session-start` | Apertura sessione | Rileva il progetto attivo, carica lo stato precedente |
| `pre-compact` | Prima della compattazione del contesto | Salva lo stato di sessione — niente va perso |
| `session-end` | Dopo ogni risposta | Persiste i file modificati e i dati di sessione |
| `cost-tracker` | Dopo ogni risposta | Traccia l'utilizzo di token e la percentuale di contesto usata |
| `desktop-notify` | Dopo ogni risposta | Notifica macOS quando Claude finisce |
| `read-tracker` | Dopo Read | Registra ogni file letto — gateguard usa questa lista per autorizzare le modifiche successive |
| `quality-gate` | Dopo Edit/Write | Esegue ruff o tsc sul file appena modificato |
| `gateguard` | Prima di Edit/Write | Blocca le modifiche cieche — forza la lettura prima |

Tutti gli hook sono definiti in `hooks/hooks.json` (sorgente di verità dello studio) e applicati agli AI tool tramite lo script di attivazione — mai modificando manualmente le config dei tool.

#### 📊 Dashboard (`scripts/dashboard.py`)

Panoramica terminale del tuo studio e del progetto attivo:

```
╭──────────────── Studio Dashboard ────────────────╮
│ jungle  /Projects/jungle  2026-06-03 21:00       │
╰──────────────────────────────────────────────────╯
  Tasks: 2 doing · 3 next
  Changelog: last 3 sessions
  Sessions: cost tracking per project
  Skills: 13 loaded
  Agents: 9 available
  Hooks: ✓ active
```

### A livello di progetto (`.studio/` in ogni repo)

| File / Cartella | Scopo | Richiesto |
|-----------------|-------|-----------|
| `STUDIO.md` | Inizia con `@~/.studio/STUDIO.md`. Aggiunge override di progetto. | ✅ Sì |
| `context.md` | Architettura, vincoli, stato delle feature attive. Non documentazione — ciò di cui l'AI ha bisogno per agire correttamente. | ✅ Sì |
| `tasks.md` | Sprint corrente: In corso / Prossimi / Bloccati. Aggiornato ogni sessione. | ✅ Sì |
| `changelog/` | Un file per sessione (`YYYY-MM-DD.md`). Cosa è stato fatto, file modificati, costo token. I 3 più recenti caricati all'inizio. | ✅ Sì |
| `gotchas.md` | Trappole note in questa codebase. Da leggere prima di eseguire. | 🔶 Se necessario |
| `memory/` | Fatti che persistono tra le sessioni. | 🔶 Se necessario |
| `agents/` | Override degli agenti specifici del progetto. | 🔶 Se necessario |
| `skills/` | Override delle skills specifiche del progetto. | 🔶 Se necessario |
| `mcp.md` | Server MCP attivi per questo progetto. | 🔶 Se necessario |

---

## 🌐 Perché AI-agnostico

Claude Code legge `CLAUDE.md`. Gemini CLI legge `GEMINI.md`. Cursor legge `.cursorrules`. Ogni tool ha il suo file di ingresso.

`.studio/` sta sotto tutti. I file di ingresso sono wrapper sottili:

```markdown
# CLAUDE.md
@.studio/STUDIO.md
```

Quando cambi tool AI, aggiorni una riga. I tuoi standard di engineering, le decisioni tecnologiche e il contesto di progetto rimangono esattamente com'erano.

Gli hook e la dashboard sono attualmente adattati per Claude Code. L'architettura è progettata per adapter aggiuntivi — vedi `scripts/activate.py --tool=`.

---

## 💰 Costo in token

Caricare il contesto globale completo all'inizio di una sessione costa circa **8.000–10.000 token** — circa il 4–5% di una finestra di contesto da 200K.

Il design mantiene questo valore basso:
- Usando imperativi, non prosa — le regole si caricano veloce, le spiegazioni no
- Caricando le skills su richiesta, non all'avvio
- Limitando il changelog agli ultimi 3 file
- Mantenendo `context.md` focalizzato sullo stato operativo, non sulla documentazione

---

## 🔄 Il protocollo di sessione

Ogni sessione segue tre fasi:

**▶ INIZIO** — Carica `tasks.md` + gli ultimi 3 file `changelog/`. Carica la modalità di contesto (dev / research / review). Conosci lo scope prima di toccare qualsiasi cosa.

**⚡ DURANTE** — Spec-first: nessuna nuova feature senza una spec approvata. IGNORE.md: nessuna eccezione. Stack: segui le decisioni, non esplorare alternative. Regole: applicate dalla modalità di contesto.

**⏹ FINE** — Sommario, file modificati, costo token. Entry del changelog scritta. Tasks aggiornate.

---

## 🏗️ Harness Engineering

Le cinque regole in `harness.md` codificano ciò che separa i sistemi AI in produzione dai demo:

1. **🔷 Schema-first** — L'output LLM validato con Pydantic o Zod prima di qualsiasi operazione.
2. **🔷 Evals-driven** — Nessun prompt va in produzione senza eseguire contro un dataset golden.
3. **🔷 Context engineering** — Il contenuto grezzo non processato non raggiunge mai l'LLM. Filtra prima.
4. **🔷 Failure-aware design** — Exception chaining, retry con backoff, recupero di risultati parziali.
5. **🔷 Observability** — Ogni chiamata LLM loggata: modello, token, latenza, costo.

---

## 🚀 Setup

### 1. Installa lo studio globale

```bash
git clone https://github.com/meowgl1/studio ~/.studio
pip install rich   # per la dashboard
```

### 2. Configura per il tuo stack

```bash
# Modifica le decisioni tecnologiche
nano ~/.studio/stack.md

# Modifica le preferenze di comunicazione
nano ~/.studio/persona.md
```

### 3. Attiva gli hook (Claude Code)

```bash
python3 ~/.studio/scripts/activate.py

# Controlla lo stato
python3 ~/.studio/scripts/activate.py --status

# Rimuovi gli hook
python3 ~/.studio/scripts/activate.py --off
```

### 4. Collega un progetto

```bash
mkdir your-project/.studio

# File di ingresso — una riga
echo "@~/.studio/STUDIO.md" > your-project/.studio/STUDIO.md

# Ingresso progetto per Claude Code — una riga
echo "@.studio/STUDIO.md" > your-project/CLAUDE.md

# Crea i file richiesti
touch your-project/.studio/context.md
touch your-project/.studio/tasks.md
mkdir your-project/.studio/changelog
```

Riempi `context.md` con l'architettura del tuo progetto, gli override dello stack e i vincoli.  
Riempi `tasks.md` con gli elementi dello sprint corrente.

### 5. Avvia la dashboard

```bash
# Dalla directory del tuo progetto
python3 ~/.studio/scripts/dashboard.py

# O da qualsiasi posto
python3 ~/.studio/scripts/dashboard.py /path/to/project
```

---

## 💬 Opinione personale

Ho costruito questo perché continuavo a perdere contesto.

Ogni nuova sessione Claude Code partiva da zero. Rispiegavo lo stack, ristabilivo i vincoli, ridescrivevo l'architettura. L'AI produceva codice tecnicamente corretto che violava decisioni che avevo preso tre sessioni prima — non perché il modello fosse scadente, ma perché non gli avevo mai dato la memoria necessaria per agire in modo coerente.

Il consiglio standard è "scrivi solo un buon CLAUDE.md." Ci ho provato. Il problema è che un buon CLAUDE.md per un progetto diventa un documento diverso da un buon CLAUDE.md per un altro progetto, e nessuno dei due sopravvive ai cambi di tool. Ogni aggiornamento era una tassa.

`.studio` risolve questo separando ciò che è stabile (standard di engineering, decisioni tecnologiche, preferenze comunicative) da ciò che cambia (task correnti, sessioni recenti, stato del progetto). Le parti stabili vivono globalmente e non hanno mai bisogno di essere riscritte.

L'altra cosa che sbagliavo prima: pensavo che l'AI avesse bisogno di documentazione. Non è così. Ha bisogno di regole. Lunghe spiegazioni sul perché usiamo Pydantic sono token sprecati. "SEMPRE validare l'output LLM con Pydantic prima di qualsiasi operazione DB" non lo è. Il passaggio dalla documentazione agli imperativi ha ridotto il contesto di inizio sessione di circa il 40% rendendo il comportamento dell'AI più coerente, non meno.

Questo è un sistema vivente. Aggiungo un gotcha quando incappo in un bug ricorrente. Aggiungo un file di memoria quando gli agenti iniziano a perdere stato importante. Aggiungo una skill quando mi ritrovo a ripetere la stessa istruzione tra sessioni. Il costo di manutenzione è inferiore al costo di non averlo.

---

## 📜 Licenza

MIT. Usalo, adattalo, spezzalo in pezzi e prendi ciò che è utile.
