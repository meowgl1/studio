# Mowgli CLI: Un'Interfaccia a Riga di Comando Multi-Provider con Routing Intelligente per Modelli Linguistici di Grandi Dimensioni

**Autore:** Thomas  
**Affiliazione:** mowgli.studio  
**Data:** Giugno 2026  
**Branch:** feat/readme-craft-skill — github.com/meowgl1/studio

---

## Abstract

Questo documento descrive la progettazione, l'implementazione e la valutazione di Mowgli CLI — un'interfaccia terminale-first e multi-provider per l'interazione con Modelli Linguistici di Grandi Dimensioni (LLM). Mowgli affronta tre problemi ricorrenti nei flussi di lavoro LLM degli sviluppatori: il consumo eccessivo di token causato dall'invio indiscriminato di ogni query al modello più costoso e capace; l'assenza di supporto per ecosistemi di provider eterogenei; la mancanza di decomposizione intelligente dei task per carichi di lavoro complessi o parallelizzabili. Il sistema implementa un classificatore multi-dimensionale, una strategia di routing a tre livelli (semplice → modello economico, complesso → pipeline sequenziale piano/esecuzione, swarm → fan-out parallelo con merge), un learning store basato su JSONL (ReasoningBank) e una pipeline di redazione PII. Le decisioni architetturali vengono comparate con Ruflo — un framework enterprise per swarm distribuiti — per contestualizzare i trade-off tra semplicità operativa e capacità di coordinazione distribuita. Il documento si conclude con una valutazione onesta di cosa il sistema fa bene, dove fallisce e quali lavori significativi rimangono aperti.

---

## 1. Introduzione

### 1.1 Motivazione

Il pattern dominante per lo sviluppo assistito da LLM nel biennio 2025–2026 è un'interfaccia chat a modello singolo: lo sviluppatore invia un messaggio, il modello più capace disponibile risponde, la risposta viene visualizzata. Questo pattern è dispendioso in due modi misurabili.

**Primo: il costo.** Una query come "cosa ritorna questa funzione?" costa 10–30 volte di più quando viene inoltrata a Claude Opus rispetto a Claude Haiku, eppure la differenza qualitativa per task di recupero fattuale è trascurabile. Gli sviluppatori che utilizzano assistenti interattivi con piani a consumo esauriscono comunemente il 20% del budget mensile con una manciata di domande esplorative — precisamente perché ogni messaggio, indipendentemente dalla complessità, raggiunge lo stesso endpoint costoso.

**Secondo: il tetto qualitativo.** I task altamente complessi — refactoring multi-file, proposte architetturali, scrittura di suite di test su un intero codebase — beneficiano della decomposizione. Un singolo modello che elabora un prompt da 2.000 token contenente cinque sub-task vagamente correlati produrrà un risultato peggiore di cinque agenti focalizzati che elaborano 400 token ciascuno, con un passaggio di sintesi finale. Eppure le interfacce chat standard non offrono alcun meccanismo di decomposizione.

Mowgli è stato costruito per risolvere entrambi i problemi nei limiti di un tool CLI: deve avviarsi in meno di un secondo, non richiedere infrastruttura persistente e comportarsi come un normale programma da terminale.

### 1.2 Scope

Mowgli **non è**:
- Un sistema multi-agente distribuito (nessuna rete, nessun protocollo di consenso)
- Un framework per il fine-tuning o la valutazione dei modelli
- Un agente autonomo che opera senza supervisione umana

Mowgli **è**:
- Un dispatcher intelligente che instrada le query umane al modello corretto automaticamente
- Un orchestratore leggero che distribuisce task parallelizzabili a più istanze modello
- Un sistema di apprendimento che registra la propria storia di routing e migliora i suggerimenti nel tempo

### 1.3 Struttura del Documento

La Sezione 2 analizza i lavori correlati. La Sezione 3 descrive l'architettura complessiva. Le Sezioni 4–8 trattano ogni sottosistema in dettaglio. La Sezione 9 valuta il sistema: vantaggi, limitazioni, funzionalità mancanti e questioni aperte. La Sezione 10 conclude con riflessioni sulla filosofia di progettazione.

---

## 2. Lavori Correlati e Posizionamento

### 2.1 Ruflo

Il confronto più rilevante per Mowgli è **Ruflo** (github.com/ruvnet/ruflo), un framework enterprise per swarm multi-agente costruito sopra Claude Code. Ruflo implementa:

- **Tre topologie swarm**: gerarchica (leader-delega), mesh (peer-to-peer) e adattiva (auto-organizzante)
- **Consenso distribuito**: algoritmo Raft per l'elezione del leader e Byzantine Fault Tolerance per ambienti non fidati
- **HNSW vector indexing**: gli agenti sono incorporati in uno spazio vettoriale semantico; le query in ingresso vengono instradate tramite ricerca del nearest neighbour approssimato
- **Pattern neurali SONA**: ottimizzazione auto-organizzante che regola le soglie di routing in modo autonomo nel tempo
- **ReasoningBank**: memoria a lungo termine basata su traiettorie che registra percorsi di ragionamento riusciti e li riutilizza
- **Sicurezza zero-trust**: comunicazione inter-agente via mTLS, verifica identità ed25519, pipeline di rilevamento PII
- **33 integrazioni MCP plugin pre-costruite**

Ruflo è operativamente pesante: richiede un database vettoriale, multipli processi worker in background e una dashboard web. È progettato per team, non per individui.

Mowgli adotta quattro dei pattern concettuali di Ruflo — fan-out swarm, scoring multi-dimensionale del task, ReasoningBank e PII scrubbing — rimpiazzando l'infrastruttura distribuita di Ruflo con equivalenti a processo singolo: threading invece di rete, JSONL invece di vector DB, regex invece di un classificatore PII basato su ML.

### 2.2 LangChain / LlamaIndex

LangChain (Harrison Chase, 2022) e LlamaIndex (Jerry Liu, 2022) forniscono framework Python per il chaining di chiamate LLM. Entrambi operano a livello di libreria: richiedono che lo sviluppatore scriva codice di orchestrazione. Mowgli inverte questa relazione — la logica di routing è dentro il tool, non nell'applicazione che lo sviluppatore sta costruendo.

### 2.3 Claude Code

Mowgli avvolge **Claude Code** (Anthropic, 2025), che è esso stesso una CLI che fornisce accesso headless ai modelli Claude tramite `--output-format stream-json`. Mowgli non è un'alternativa a Claude Code; è un meta-layer che decide quale modello Claude Code debba usare, gestisce la continuità della sessione tra i turn e aggiunge un'astrazione a livello provider così che le chiamate Gemini CLI possano essere mescolate.

### 2.4 Sommario del Posizionamento

| Sistema | Livello | Infrastruttura | Multi-provider | Auto-routing | Swarm |
|---|---|---|---|---|---|
| Claude Code | CLI | Nessuna | No | No | No |
| Gemini CLI | CLI | Nessuna | No | No | No |
| LangChain | Libreria | Nessuna | Sì | Manuale | No |
| Ruflo | Framework | DB + worker + dashboard | Sì | SONA self-learning | Sì (distribuito) |
| **Mowgli** | **CLI** | **Nessuna** | **Sì** | **Classificatore multi-dim** | **Sì (threaded)** |

---

## 3. Architettura del Sistema

### 3.1 Mappa dei Moduli

```
src/mowgli/
├── cli.py             Entry point Click; routing verso REPL o modalità pipe headless
├── repl.py            MowgliREPL — main event loop, esecuzione turni, comandi slash
├── router.py          Classificatore multi-dimensionale, RouterConfig, ClassifyResult
├── swarm.py           Esecutore fan-out parallelo con decomposizione e merge
├── reasoning_bank.py  Learning store JSONL; suggerisce modelli dalla storia
├── pii_scrubber.py    Pipeline di redazione regex
├── config.py          ModelSpec, MowgliConfig, registro modelli con override
├── branding.py        Banner terminale, testo /help
├── game.py            Easter egg dino pixel (30fps, gravità, hi-score)
├── mcp_manager.py     Abilitazione/disabilitazione MCP server a runtime
└── providers/
    ├── base.py        Protocollo Provider, dataclass StreamState, StreamEvent
    ├── claude.py      ClaudeProvider — wrappa claude CLI via subprocess
    └── gemini.py      GeminiProvider — wrappa gemini CLI via subprocess
```

### 3.2 Flusso dei Dati

```
Input utente
    │
    ▼
[PII scrubber]          ← redazione regex prima di qualsiasi chiamata esterna
    │
    ▼
[Router.classify()]     ← chiamata haiku (~50 token); ritorna ClassifyResult JSON
    │
    ├─ simple   → [modello simple_alias]  sessione fresca, headless, economico
    │
    ├─ complex  → [plan: opus]  →  [execute: sonnet]  pipeline sequenziale
    │
    └─ swarm    → [decompose: haiku]
                     │
                 [N × worker: haiku]  thread paralleli
                     │
                 [merge: sonnet]
    │
    ▼
[ReasoningBank.record()]  ← log metadati turn su JSONL
    │
    ▼
Output al terminale
```

### 3.3 Modello di Sessione

Mowgli distingue tra **modello di sessione** (il modello con cui l'utente interagisce quando il routing è disabilitato) e **modello instradato** (il modello selezionato dal router per un turno specifico). Quando il routing è abilitato, le query semplici vengono eseguite in una sessione fresca e stateless sul modello economico. Le query complesse e swarm usano anch'esse sessioni fresche perché la pipeline crea il proprio contesto. La continuità di sessione (via `--resume <session_id>`) è preservata solo in modalità "router off", dove l'utente ha scelto un singolo modello per un'intera conversazione.

Questa è una scelta di progetto deliberata con un trade-off significativo, discusso nella Sezione 9.

---

## 4. Router: Classificazione Multi-Dimensionale

### 4.1 Razionale del Design

La prima versione del router di Mowgli (v2.3) usava un classificatore binario: la query veniva inviata a Haiku con il prompt `"Rispondi con esattamente una parola: SIMPLE o COMPLEX"`. Questo presentava due fallimenti critici.

**Fallimento 1: Nessuno scoring dell'astrazione.** Una query di una riga come "Spiega il teorema CAP e le sue implicazioni per il consenso distribuito in ambienti Bizantini" veniva classificata regolarmente SIMPLE perché era breve. Al contrario, una domanda procedurale verbosa su una singola funzione veniva classificata COMPLEX per via della sua lunghezza. Il classificatore misurava il conteggio dei token, non la difficoltà intellettuale.

**Fallimento 2: Nessun rilevamento del parallelismo.** Il sistema non aveva modo di identificare che un task fosse decomponibile. "Scrivi i test per le funzioni A, B, C, D ed E" veniva instradato verso complex (plan → execute), producendo output sequenziale, quando i cinque sub-task erano completamente indipendenti e avrebbero potuto girare in parallelo.

Il classificatore v2.4 affronta entrambi i problemi ritornando JSON strutturato su quattro dimensioni ortogonali.

### 4.2 Schema ClassifyResult

```python
@dataclass
class ClassifyResult:
    effort:   int    # 1–10: costo cognitivo/ingegneristico per rispondere bene
    tools:    int    # chiamate tool stimate necessarie (0 = solo testo)
    domain:   str    # conversational | factual | code | architectural | creative
    parallel: bool   # true se il task contiene sub-task indipendenti
    route:    str    # simple | complex | swarm
```

Il modello classificatore (Haiku per default) riceve:

```
Analizza la seguente query utente e ritorna un oggetto JSON — nient'altro.

Campi:
  effort   (int 1-10): sforzo cognitivo/ingegneristico richiesto
  tools    (int 0-N):  chiamate tool stimate necessarie
  domain   (str):      conversational | factual | code | architectural | creative
  parallel (bool):     true se il task contiene sub-task indipendenti
  route    (str):      simple | complex | swarm

Regole di routing:
  simple  → effort ≤ 4 AND tools ≤ 1
  swarm   → effort ≥ 7 AND parallel is true
  complex → tutto il resto
```

### 4.3 Soglie di Routing

| Condizione | Route | Modelli |
|---|---|---|
| effort ≤ 4 AND tools ≤ 1 | simple | `simple_alias` (default: haiku) |
| effort ≥ 7 AND parallel=true | swarm | N×`swarm_worker_alias` → `swarm_merge_alias` |
| else | complex | plan:`complex_plan_alias` → execute:`complex_execute_alias` |

Le soglie sono hard-coded in v2.4. Dovrebbero diventare apprendibili tramite ReasoningBank in una versione futura (vedi Sezione 9.4).

### 4.4 Il Bug di simple_alias (Storico)

Prima della v2.4, il router conteneva un bug di correttezza silenzioso. In `_execute_turn()`:

```python
# v2.3 — con bug
if route == "complex":
    self._execute_pipe(...)
    return None
else:
    self.console.print(f"  ⎇ simple → {self.router.simple_alias}")
    # CADUTA ATTRAVERSO — usa self.model_spec, NON simple_alias!
```

Il log mostrava `⎇ simple → haiku` mentre in realtà eseguiva la richiesta usando Sonnet (il default di sessione). Questo causava sovracosti del 3–5× su ogni query semplice. Il fix aggiunge un branch esplicito che costruisce gli argomenti da `simple_spec = config.resolve_model(self.router.simple_alias)` prima del dispatch.

---

## 5. Swarm: Fan-Out Parallelo con Merge

### 5.1 Fondamento Concettuale

Il pattern swarm affronta l'osservazione che molti task degli sviluppatori sono implicitamente paralleli. Fare il refactoring di dieci file è un composto di dieci task indipendenti. Tradurre un codebase in un altro linguaggio è N unità di traduzione indipendenti. Scrivere una suite di test è un test per funzione, scrivibili indipendentemente.

Le interfacce LLM standard elaborano queste richieste in modo sequenziale perché mantengono un singolo thread di conversazione. Il modulo swarm di Mowgli rompe questo vincolo.

Il design è direttamente ispirato all'architettura swarm di Ruflo, specificamente la topologia fan-out dove un coordinatore decompone un task, più worker lo eseguono in parallelo e un agente di sintesi unisce i risultati. La differenza chiave è nel layer implementativo: i worker di Ruflo sono agenti distribuiti che comunicano via mTLS; i worker di Mowgli sono thread che generano chiamate subprocess sulla macchina locale.

### 5.2 Pipeline di Esecuzione

```
Task (prompt utente)
    │
    ▼
[Decompositor — haiku]
  Prompt: "Dividi questo task in esattamente N sub-task indipendenti.
           Ritorna SOLO un array JSON di N stringhe."
    │
    ▼
[sub_prompts: list[str]]  — N stringhe
    │
    ├─ Thread 0: subprocess → haiku → result_0
    ├─ Thread 1: subprocess → haiku → result_1
    └─ Thread N: subprocess → haiku → result_N
    │
    ▼ (join tutti i thread, timeout=130s)
[Prompt merge → sonnet]
  "Sei un agente di sintesi. Unisci questi N output in un'unica
   risposta coerente e deduplicata. Risolvi le contraddizioni."
    │
    ▼
Output finale
```

### 5.3 Fallback della Decomposizione

Se il decompositor non riesce a ritornare un array JSON valido (errore di parsing, timeout, lunghezza errata), la strategia di fallback è inviare il prompt originale invariato a tutti gli N worker. Questo produce output ridondanti ma garantisce che il passaggio di merge abbia comunque del materiale con cui lavorare. Il modello di merge (Sonnet) è atteso deduplicare correttamente.

### 5.4 Override Manuale

Il comando slash `/swarm` bypassa il router automatico:

```
/swarm scrivi una docstring per ogni funzione pubblica in src/mowgli/
/swarm 5 traduci tutti i messaggi di errore in spagnolo
```

Il prefisso intero opzionale sovrascrive `router.swarm_workers` solo per quella chiamata.

### 5.5 Limitazioni dell'Implementazione Attuale

Il modello threading ha un tetto fisso alla concorrenza della macchina locale. Una macchina a 16 core può realisticamente eseguire 8–10 worker subprocess simultaneamente prima che l'I/O diventi il bottleneck. Ancora più importante: i risultati dei worker vengono attualmente raccolti integralmente prima del merge — non c'è streaming merge. L'utente non vede nulla finché tutti gli N worker non completano. Per task grandi, questa latenza è significativa.

---

## 6. ReasoningBank: Apprendimento Leggero

### 6.1 Motivazione

Ruflo implementa un learning store basato su traiettorie supportato da un database vettoriale. L'obiettivo è imparare, nel tempo, quali agenti e modelli funzionano meglio per quali categorie di problema — e usare questa storia per migliorare le future decisioni di routing senza configurazione manuale.

Il ReasoningBank di Mowgli è lo stesso concetto implementato senza infrastruttura. Il vincolo è zero-dependency: il bank deve funzionare su qualsiasi macchina senza servizi aggiuntivi.

### 6.2 Schema del Record

```jsonl
{
  "ts": "2026-06-13T09:14:22.331Z",
  "domain": "code",
  "effort": 4,
  "tools": 2,
  "parallel": false,
  "route": "simple",
  "model": "haiku",
  "cost_usd": 0.0003,
  "quality": null
}
```

Il campo `quality` è lasciato null al momento della scrittura. Tool futuri — un comando `/rate`, o annotazione post-hoc — potranno riempirlo retroattivamente. Nel frattempo, il bank usa il costo come proxy inverso della qualità: risposte meno costose per lo stesso profilo domain/effort sono debolmente preferite.

### 6.3 Algoritmo di Suggerimento Modello

```python
def suggest_model(domain, effort, config_models):
    matches = [r for r in load() if r.domain == domain and abs(r.effort - effort) <= 2]
    if len(matches) < 5:
        return None  # dati insufficienti

    scores = {}
    for r in matches:
        score = r.quality if r.quality is not None else max(0, 1.0 - r.cost_usd * 1000)
        scores.setdefault(r.model, []).append(score)

    return max(scores, key=lambda m: mean(scores[m]))
```

La tolleranza `±2 di effort` significa che un record del bank da un task di effort=5 informa i suggerimenti per query di effort=3–7 nello stesso dominio. Questo affronta la scarsità di dati nelle sessioni iniziali.

### 6.4 Cosa il Bank Attualmente Non Fa

- **Influenzare il routing automaticamente**: `suggest_model()` è implementato ma non è ancora collegato a `classify()` come override. Il bank raccoglie dati ma non cambia ancora le decisioni di routing. Questo è intenzionale — il dataset deve crescere prima che gli override automatici siano affidabili.
- **Gestire la qualità del contesto multi-turn**: i punteggi di qualità, quando eventualmente raccolti, non possono facilmente tenere conto se una risposta era buona perché il modello è bravo o perché aveva contesto utile dai turn precedenti.

---

## 7. PII Scrubber

### 7.1 Threat Model

Lo scrubber affronta una minaccia specifica e circoscritta: uno sviluppatore copia un blocco di codice contenente una credenziale nel prompt di Mowgli, e quella credenziale viene trasmessa a un'API LLM remota dove potrebbe essere registrata.

Non è un sistema di sicurezza esaustivo. Non previene:
- L'esfiltrazione semantica (descrivere una password senza scriverla)
- L'avvelenamento progressivo del contesto attraverso i turn
- L'iniezione di prompt dai risultati di tool esterni

Affronta il pattern di esposizione accidentale più comune.

### 7.2 Copertura dei Pattern

| Categoria | Esempio | Sostituzione |
|---|---|---|
| Chiave OpenAI | `sk-abc123...` | `[OPENAI_KEY]` |
| Chiave Anthropic | `sk-ant-...` | `[ANTHROPIC_KEY]` |
| Chiave API Google | `AIza...` | `[GOOGLE_KEY]` |
| AWS Key ID | 20 char maiuscole | `[AWS_KEY_ID]` |
| AWS Secret | 40 char base64 | `[AWS_SECRET]` |
| Token GitHub | `ghp_`, `gho_`, `github_pat_` | `[GITHUB_TOKEN]` |
| Bearer token | `Bearer <token>` | `Bearer [TOKEN]` |
| JWT | Tre segmenti base64url | `[JWT]` |
| Chiavi private PEM | Blocco `-----BEGIN PRIVATE KEY-----` | `[PRIVATE_KEY]` |
| Indirizzi email | `user@dominio.tld` | `[EMAIL]` |
| Segreti hex | 32+ char hex | `[SECRET]` |

### 7.3 Rischio di Falsi Positivi

I pattern AWS sono i più aggressivi: il pattern a 20 caratteri maiuscoli intercetta gli AWS Access Key ID ma potrebbe anche catturare identificatori o costanti in maiuscolo nel codice. Il pattern a 40 caratteri base64 per i segreti AWS potrebbe intercettare hash SHA-1 o dati binari codificati in base64.

Le versioni future dovrebbero permettere l'opt-out per singolo pattern tramite `~/.studio/mowgli/scrubber.json`.

---

## 8. Astrazione Provider

### 8.1 Definizione del Protocollo

Sia i provider Claude che Gemini implementano il protocollo `Provider`:

```python
class Provider(Protocol):
    name: str

    def build_headless_args(
        self,
        prompt: str,
        model_id: str,
        session_id: str,
        resume: bool = False,
        include_partial: bool = True,
        system_prompt: str | None = None,
    ) -> list[str]: ...

    def parse_stream_line(self, line: str, state: StreamState) -> StreamEvent | None: ...

    def run_interactive(self, model_id: str) -> None: ...
```

I provider non chiamano le API direttamente — costruiscono liste di argomenti per l'invocazione subprocess delle CLI sottostanti (`claude` e `gemini`). Questo significa che Mowgli eredita tutta la gestione delle credenziali, del rate limiting, della configurazione dei server MCP, dei permessi e delle definizioni dei tool dalle CLI upstream. Il costo è che Mowgli è strettamente accoppiato alle versioni binarie delle CLI.

### 8.2 StreamState e StreamEvent

```python
class StreamState:
    printed_text_len: int     # deduplica eventi testo cumulativi
    seen_tool_ids: set[str]   # deduplica eventi tool_use
    last_char_newline: bool   # traccia posizione cursore terminale
    session_id: str | None    # impostato dall'evento init

class StreamEvent:
    type: str         # text_delta | tool_use | tool_result | cost | error
    content: str
    tool_name: str | None
    tool_input: dict | None
    cost_usd: float
```

Il formato stream-json usato da Claude Code emette testo cumulativo (non delta), quindi `printed_text_len` è usato per calcolare la porzione incrementale. Gli eventi tool use sono deduplicati per ID perché la stessa chiamata tool potrebbe apparire in multipli eventi stream mentre l'input viene progressivamente completato.

### 8.3 Limitazioni del Provider Gemini

Il provider Gemini assume che la CLI `gemini` esponga un'interfaccia simile a quella di Claude Code (`-p`, `-o stream-json`, `-m`, `--session-id`, `--resume`). In pratica, il formato stream-json esatto della Gemini CLI potrebbe differire. Il parametro `system_prompt` aggiunto in v2.4 è accettato dalla firma del metodo per conformità al Protocollo ma non viene inoltrato, poiché la Gemini CLI non espone un flag equivalente a `--append-system-prompt`.

---

## 9. Valutazione

### 9.1 Cosa Funziona Bene

**Riduzione dei costi.** Il valore più immediato del router è economico. Una tipica sessione di sviluppo da 30 query — per lo più ricerche fattuali, brevi spiegazioni di codice e fix rapidi — conterrà circa 20 query semplici e 10 complesse. Con il vecchio approccio a modello singolo (Sonnet per tutto), le 20 query semplici consumano token Sonnet a ~$0,003/1K. Con il routing abilitato, quelle 20 query vengono instradate verso Haiku a ~$0,00025/1K — una riduzione dei costi di 12× sul 67% del traffico. Risparmi reali di token del 60–70% per sessione sono raggiungibili su tipici carichi di lavoro di sviluppo.

**Zero overhead operativo.** Mowgli non richiede database, daemon o configurazione prima del primo utilizzo. `pip install -e .` seguito da `mowgli` è il flusso di onboarding completo. Questo è non banale: il costo in termini di produttività dello sviluppatore per configurare e mantenere un'infrastruttura è spesso maggiore del costo dell'inefficienza che l'infrastruttura avrebbe dovuto risolvere.

**Routing trasparente.** Ogni turn instradato stampa la sua classificazione inline:

```
  ⎇ complex  effort:8 tools:5 domain:architectural
```

L'utente sa sempre quale modello sta rispondendo e perché. Questo costruisce fiducia nelle decisioni del router e rende immediatamente visibili le classificazioni errate.

**Protezione PII come default.** La maggior parte degli sviluppatori non pensa all'esposizione di credenziali quando incolla codice in un'interfaccia chat. Avere lo scrubber eseguito silenziosamente ad ogni turn fornisce protezione senza richiedere che l'utente ci pensi.

### 9.2 Debolezze Note

**Costo della classificazione.** Ogni turn innesca una chiamata Haiku per la classificazione prima che la query effettiva venga eseguita. Questo aggiunge ~0,5–2 secondi di latenza e un piccolo costo non nullo in token (~50 token input + ~30 output). Per query conversazionali molto veloci, l'overhead di classificazione potrebbe superare il costo di instradare semplicemente tutto verso Haiku.

Un'ottimizzazione futura: pre-filtro euristico prima della classificazione. Se la query è sotto 20 token e non contiene blocchi di codice o percorsi di file, classificare come simple senza la chiamata API.

**Perdita di continuità della sessione.** Quando il routing è abilitato, ogni turn in modalità "simple" usa una sessione fresca. Questo significa che il modello non ha memoria dei turn precedenti. Un utente che chiede "qual è la capitale della Francia?" (simple → haiku, sessione A) e poi "e qual è la sua popolazione?" (simple → haiku, sessione B) riceverà una risposta scorretta perché il pronome "sua" non ha riferimento nella seconda sessione.

Questa è la più significativa falla di usabilità nell'architettura attuale. Il trade-off è stato fatto deliberatamente: supportare la continuità della sessione tra modelli instradati richiede o di mantenere ID di sessione separati per modello (overhead di memoria, semantica di reset poco chiara) o di instradare sempre i turn dello stesso modello alla stessa sessione (rompendo le chiamate swarm e pipeline). Non esiste una soluzione pulita che preservi sia l'efficienza dei costi che la continuità conversazionale senza un layer di session management più sofisticato.

**Opacità della latenza swarm.** Durante un'esecuzione swarm, l'utente vede "launching N workers…" e poi nulla finché tutti i worker completano. Per un task 3-worker × 60 secondi, l'utente attende 60 secondi senza feedback. Lo streaming del progresso dei worker migliorerebbe significativamente la reattività percepita.

**Allucinazione del classificatore.** La classificazione JSON è prodotta da Haiku, che occasionalmente restituisce JSON malformato, avvolge la risposta in code fence markdown, o include prosa esplicativa. Il parser tenta di estrarre la prima sottostringa `{...}` e ricade su `ClassifyResult.fallback()` in caso di fallimento. Il fallback instrada verso complex — conservativo ma aggiunge costi non necessari quando la query era effettivamente semplice.

**Il ReasoningBank non influenza ancora il routing.** Il bank raccoglie dati ma `suggest_model()` non è collegato a `classify()`. Questo significa che il sistema di apprendimento è passivo — osserva ma non agisce. Collegare i due è la funzionalità a più alta priorità per la v2.5.

### 9.3 Cosa Manca

Le seguenti funzionalità sono identificate come lacune significative, non omissioni cosmetiche:

**1. Loop di feedback qualitativo.**
Il campo `quality` nei record del ReasoningBank è sempre null. Senza un meccanismo per valutare le risposte (anche un semplice comando `/rate` post-turn), il suggerimento modello del bank degrada a pura minimizzazione dei costi anziché routing aggiustato per qualità.

**2. Soglie di routing adattive.**
Le soglie (`effort ≤ 4` per simple, `effort ≥ 7` per swarm) sono costanti hard-coded. In Ruflo, i pattern SONA le regolano autonomamente in base al feedback sui risultati. Mowgli dovrebbe imparare dal bank: se le query di effort=5 instradate verso complex producono consistentemente risposte di bassa qualità, abbassare la soglia del complex.

**3. Streaming del progresso swarm.**
I worker completano in modo asincrono ma i risultati vengono elaborati in batch. Un'interfaccia streaming — che mostri output parziale da ciascun worker non appena arriva, poi sintetizzi — renderebbe le chiamate swarm interattive anziché opache.

**4. Coerenza del routing multi-turn.**
Il router tratta ogni turn in modo indipendente. Non considera: quale modello ha risposto al turn precedente? La query corrente è un follow-up che richiede lo stesso contesto? Implementare una memoria di routing a livello di turn prevenga i fallimenti di continuità conversazionale descritti nel 9.2.

**5. Consapevolezza delle capacità del provider.**
Il router può assegnare qualsiasi query a qualsiasi modello senza verificare se quel modello possa eseguire il task. Assegnare un task complesso di generazione codice con 15 chiamate tool a `gemini-lite` (finestra di contesto limitata) potrebbe fallire silenziosamente. Un registro delle capacità che mappa modello → max_context / tool_support / code_execution permetterebbe al router di escludere modelli incompatibili.

**6. Stabilità Obsidian MCP.**
Il server Obsidian MCP (MCPVault, configurato nella v2.3) ha riportato fallimenti intermittenti. La causa radice non è stata ancora investigata al momento della stesura. La salute del server MCP non è monitorata da Mowgli — i server falliti falliscono silenziosamente dalla prospettiva dell'utente.

**7. Copertura dei test per i nuovi moduli.**
router.py, swarm.py, reasoning_bank.py e pii_scrubber.py non hanno copertura a livello di unit test. La suite di test esistente (72 test per il codebase pre-v2.4) non copre nessuna delle aggiunte della v2.4. Questo è un debito tecnico significativo.

**8. Gestione del budget token.**
Non esiste un meccanismo per impostare un tetto di spesa per sessione o per turn. Un utente che attiva accidentalmente 10 chiamate swarm non riceve nessun avviso. Implementare un `max_session_cost_usd` configurabile che interrompa l'esecuzione previene addebiti inaspettati.

### 9.4 Decisioni di Design: Razionale

**Perché subprocess invece di chiamate SDK?**
Mowgli dispatcha ai binari CLI `claude` e `gemini` tramite subprocess anziché chiamare direttamente l'Anthropic SDK o l'API Gemini. Questa scelta preserva tutta la gestione delle credenziali, il rate limiting, la configurazione dei server MCP, i permessi e le definizioni dei tool che le CLI upstream forniscono. Il costo è che Mowgli è strettamente accoppiato alle versioni dei binari CLI. Il vantaggio è che una nuova sessione Mowgli eredita automaticamente qualsiasi configurazione Claude Code che l'utente ha impostato — tool, permessi, server MCP — senza che Mowgli debba replicare quella configurazione.

**Perché JSONL invece di SQLite o un vector DB?**
Il JSONL è universalmente leggibile con `tail -f`, `jq` o qualsiasi editor di testo. Non richiede migrazione dello schema, linguaggio di query o dipendenze esterne. Il ReasoningBank a 500 record (la finestra rolling configurata) è circa 50KB — banale da leggere interamente in memoria ad ogni chiamata di suggerimento. Le caratteristiche di performance sono adeguate per la scala di utilizzo prevista (centinaia o migliaia di record per sviluppatore al mese). SQLite aggiungerebbe flessibilità di query; un vector DB aggiungerebbe ricerca semantica. Nessuno dei due fornisce abbastanza valore marginale da giustificare l'aumento di complessità.

**Perché non adottare i protocolli di consenso di Ruflo?**
Il consenso Raft e il Byzantine Fault Tolerance sono soluzioni corrette per sistemi distribuiti dove gli agenti girano su macchine separate con partizioni di rete e condizioni avversariali. Per una CLI a singolo sviluppatore dove tutti gli "agenti" sono thread che generano subprocess sulla stessa macchina, questi protocolli aggiungono latenza, complessità e modi di fallimento senza fornire nessuno dei loro benefici intesi. La decisione di usare il threading è una limitazione deliberata dello scope: Mowgli è un tool personale, non un sistema distribuito.

**Perché le soglie del router non sono configurabili tramite file di configurazione?**
Nell'implementazione attuale, i default di RouterConfig sono hard-coded in `router.py` e mutabili solo a runtime tramite l'API Python o il comando `/router`. Un file di configurazione `~/.studio/mowgli/router.json` sarebbe il meccanismo corretto per la personalizzazione persistente. Questo è stato rimandato per evitare un'espansione prematura delle funzionalità prima che la logica di routing stessa venga validata dall'utilizzo reale.

---

## 10. Conclusione

Mowgli CLI affronta un problema reale e misurabile: l'omogenizzazione delle query LLM in chiamate a modello singolo, provider singolo e complessità singola. Introducendo un classificatore multi-dimensionale, tre tier di routing, esecuzione swarm parallela e un learning store passivo, cattura una frazione significativa dei miglioramenti di costo e qualità raggiungibili tramite dispatch intelligente — rimanendo al contempo un tool terminale a singolo comando e zero infrastruttura.

Il confronto con Ruflo è istruttivo in entrambe le direzioni. Ruflo dimostra cosa è possibile quando è disponibile un'infrastruttura distribuita completa: topologie auto-organizzanti, validazione delle decisioni basata su consenso, ricerca agenti indicizzata vettorialmente. Mowgli dimostra cosa è raggiungibile senza nulla di tutto questo, per un singolo sviluppatore a un terminale. I pattern di Ruflo che si sono tradotti — fan-out swarm, scoring multi-dimensionale, log delle traiettorie, PII scrubbing — hanno dimostrato che gli insight concettuali dei sistemi multi-agente enterprise sono separabili dalla loro complessità operativa.

La valutazione più onesta del sistema attuale: la logica di routing è solida ma il sistema di apprendimento è passivo, la UX dello swarm è opaca e il trade-off sulla continuità della sessione crea una classe di fallimento conversazionale che frustrerà gli utenti che si aspettano interazioni multi-turn coerenti. Queste sono deficienze note, non incognite sconosciute. Il percorso dalla v2.4 a uno strumento di qualità production richiede di chiuderle sistematicamente.

---

## Riferimenti

1. Ruflo — ruvnet, 2026. *Ruflo: Enterprise Multi-Agent Swarm Framework*. github.com/ruvnet/ruflo

2. Anthropic, 2025. *Claude Code: Command-Line Interface for Claude*. claude.ai/code

3. Google, 2025. *Gemini CLI*. github.com/google-gemini/gemini-cli

4. Chase, H., 2022. *LangChain*. github.com/langchain-ai/langchain

5. Liu, J., 2022. *LlamaIndex (ex GPT Index)*. github.com/run-llama/llama_index

6. Lamport, L., Shostak, R., Pease, M., 1982. *The Byzantine Generals Problem*. ACM Transactions on Programming Languages and Systems, 4(3):382–401.

7. Ongaro, D., Ousterhout, J., 2014. *In Search of an Understandable Consensus Algorithm (Raft)*. USENIX ATC '14.

8. Malkov, Y.A., Yashunin, D.A., 2018. *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs (HNSW)*. IEEE Transactions on Pattern Analysis and Machine Intelligence.

9. OWASP, 2025. *OWASP Top 10 for Large Language Model Applications*.

10. mowgli.studio, 2026. *Studio — rules, contexts, hooks, agents, skills, dashboard*. github.com/meowgl1/studio

---

*Questo documento è stato prodotto nell'ambito del progetto studio su mowgli.studio. L'implementazione descritta è disponibile su github.com/meowgl1/studio sul branch `feat/readme-craft-skill`.*
