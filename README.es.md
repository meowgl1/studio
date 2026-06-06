# .studio

> Un sistema de gestión de contexto agnóstico de IA para proyectos de software.

🌍 [English](README.md) · [Italiano](README.it.md) · [Español](README.es.md)

---

## 🧠 Qué es

`.studio` es una carpeta estructurada de archivos markdown que le da a cualquier asistente de codificación IA — Claude Code, Gemini CLI, Cursor, o cualquier otro — una comprensión consistente y estratificada de cómo trabajas, antes de que escriba una sola línea de código.

No es un plugin. No es un framework. Es un conjunto de archivos.

---

## 🙏 Reconocimientos

La expansión v2.0 de este sistema fue inspirada por **[ECC](https://github.com/affaan-m/ECC)** de [@affaan-m](https://github.com/affaan-m), ganador del hackathon de Claude. ECC demostró cómo se ve un sistema de contexto IA completamente operativo a escala — 97 agentes, 300+ skills, 20+ hooks, y soporte cross-tool en 7 plataformas de IA.

Este proyecto tomó una dirección diferente: en lugar de un sistema con CLI pesada, `.studio` adapta los patrones más valiosos de ECC en una capa ligera, nativa de Python y agnóstica de IA. La arquitectura de reglas, los modos de contexto, la infraestructura de hooks y el diseño de agentes fueron todos moldeados estudiando el enfoque de ECC.

---

## ⚙️ Cómo funciona

Cada sesión IA en un proyecto comienza con una cascada:

```
project/CLAUDE.md (o GEMINI.md, .cursorrules, etc.)
  └── @.studio/STUDIO.md              ← contexto del proyecto
        └── @~/.studio/STUDIO.md      ← estándares globales
              ├── harness.md           ← reglas de engineering
              ├── stack.md             ← decisiones tecnológicas
              ├── persona.md           ← estilo de comunicación
              ├── IGNORE.md            ← archivos que nunca tocar
              ├── evals.md             ← métricas de éxito de agentes
              ├── rules/               ← reglas por lenguaje
              ├── contexts/            ← comportamiento por modo
              ├── skills/              ← procedimientos reutilizables
              └── agents/              ← subagentes especializados
```

El tool de IA lee el archivo de entrada, que expande todas las referencias `@` en secuencia. Cuando el modelo lee tu primer mensaje, ya conoce tus estándares de engineering, stack tecnológico, reglas activas y cómo prefieres comunicarte.

El `~/.studio/` global se aplica a todos los proyectos en tu máquina. El `.studio/` de cada proyecto hereda del global y añade su propio contexto — arquitectura, sprint actual, trampas conocidas.

---

## 🗂️ Estructura

### Global (`~/.studio/`)

#### 📌 Estándares

| Archivo | Propósito |
|---------|-----------|
| `STUDIO.md` | Punto de entrada. Referencia todos los archivos globales. Define el protocolo de sesión, puntos de extensión, agentes y skills disponibles. |
| `harness.md` | Cinco absolutos de engineering: schema-first, evals-driven, context engineering, failure-aware, observability. |
| `stack.md` | Decisiones tecnológicas — definitivas, no sugerencias. Python, TypeScript, Next.js, Supabase. Sin LangChain. |
| `persona.md` | Contrato de comunicación. Directo, code-first, sin cortesías, italiano o inglés por sesión. |
| `IGNORE.md` | Archivos que la IA nunca debe modificar: `.env*`, `.git/`, build artifacts, migrations. |
| `evals.md` | Cómo saber si los agentes están teniendo éxito. Reglas de logging de sesión. |

#### 📏 Reglas (`rules/`)

Estándares de código aplicables, cargados en cada sesión. Organizados por scope:

| Carpeta | Contenido |
|---------|-----------|
| `rules/common/` | `clean-code` · `clean-architecture` · `testing` · `performance` · `patterns` · `security` · `llm-security` · `git` · `hooks` |
| `rules/python/` | `coding-style` · `patterns` · `testing` · `security` · `fastapi` |
| `rules/js/` | `coding-style` · `patterns` · `testing` · `security` · `react` |
| `rules/sql/` | `coding-style` · `patterns` · `security` |

#### 🎭 Contextos (`contexts/`)

Archivos de comportamiento por modo. Carga el que corresponde a tu actividad actual:

| Archivo | Cuándo usarlo |
|---------|---------------|
| `contexts/dev.md` | Estás construyendo o corrigiendo código activamente |
| `contexts/research.md` | Estás investigando una codebase o un problema |
| `contexts/review.md` | Estás revisando un PR o auditando código |

Cada archivo de contexto activa las reglas relevantes y define el comportamiento apropiado para ese modo.

#### 🛠️ Skills (`skills/`)

Procedimientos reutilizables invocados por nombre durante las sesiones:

| Skill | Propósito |
|-------|-----------|
| `spec-driven-development` | Flujo de trabajo spec-first — obligatorio antes de cualquier nueva feature |
| `webapp-testing` | Setup y patrones de testing E2E con Playwright |
| `backend-patterns` | API design, service layer, repository, auth, caching |
| `frontend-patterns` | Next.js App Router, Server Components, data fetching |
| `docker-patterns` | Builds multi-stage, Compose para dev local, hardening de seguridad |
| `api-design` | Convenciones REST, formato de respuesta, paginación, versionado |
| `coding-standards` | Setup de linting, pre-commit hooks, CI enforcement |
| `git-workflow` | Estrategia de branching, disciplina en commits, proceso de PR |
| `security-review` | Checklist OWASP — ejecutar antes de mergear código de auth/pago |
| `eval-harness` | Construir harnesses de evaluación para features de IA/LLM |
| `tracker` | Logging de costos y tokens por sesión |
| `caveman` | Patrones de scripting mínimos, sin dependencias |
| `multi-agent-patterns` | Cuándo y cómo spawnear subagentes — plantillas de handoff, reglas para trabajo en paralelo, anti-patrones |

#### 🤖 Agentes (`agents/`)

Subagentes especializados invocados por nombre. Cada uno tiene un rol definido y un formato de salida:

| Agente | Propósito |
|--------|-----------|
| `architect` | System design, ADRs, análisis de trade-offs, planificación de escalabilidad |
| `planner` | Descomponer requerimientos en planes de implementación por fases |
| `tdd-guide` | Enforcement test-first — escribe los tests antes de la implementación |
| `performance-optimizer` | Encontrar y corregir queries N+1, endpoints lentos, bundle bloat |
| `security-reviewer` | Respuesta a incidentes de seguridad y auditorías profundas |
| `refactor-cleaner` | Mejorar la estructura sin cambiar el comportamiento |
| `code-explorer` | Mapear codebases no familiares — entry points, patrones, trampas |
| `code-simplifier` | Eliminar abstracciones prematuras y complejidad innecesaria |
| `doc-updater` | Mantener context.md, gotchas.md y README sincronizados con el código |

#### 🪝 Hooks (`hooks/`, `scripts/`)

Automatización que se ejecuta alrededor de tus sesiones IA:

| Hook | Trigger | Qué hace |
|------|---------|----------|
| `session-start` | Apertura de sesión | Detecta el proyecto activo, carga el estado previo |
| `pre-compact` | Antes de la compactación del contexto | Guarda el estado de sesión — nada se pierde |
| `session-end` | Después de cada respuesta | Persiste los archivos modificados y los datos de sesión |
| `cost-tracker` | Después de cada respuesta | Rastrea el uso de tokens y la utilización de la ventana de contexto |
| `desktop-notify` | Después de cada respuesta | Notificación macOS cuando Claude termina |
| `read-tracker` | Después de Read | Registra cada archivo leído — gateguard usa esta lista para autorizar ediciones posteriores |
| `quality-gate` | Después de Edit/Write | Ejecuta ruff o tsc en el archivo recién modificado |
| `gateguard` | Antes de Edit/Write | Bloquea ediciones ciegas — fuerza la lectura primero |

Todos los hooks están definidos en `hooks/hooks.json` (fuente de verdad del studio) y aplicados a los tools de IA mediante el script de activación — nunca editando manualmente las configs de los tools.

#### 📊 Dashboard (`scripts/dashboard.py`)

Vista general en terminal de tu studio y proyecto activo:

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

### A nivel de proyecto (`.studio/` en cada repo)

| Archivo / Carpeta | Propósito | Requerido |
|-------------------|-----------|-----------|
| `STUDIO.md` | Comienza con `@~/.studio/STUDIO.md`. Añade overrides del proyecto. | ✅ Sí |
| `context.md` | Arquitectura, restricciones, estado de features activas. No documentación — lo que la IA necesita para actuar correctamente. | ✅ Sí |
| `tasks.md` | Sprint actual: En curso / Próximos / Bloqueados. Actualizado cada sesión. | ✅ Sí |
| `changelog/` | Un archivo por sesión (`YYYY-MM-DD.md`). Qué se hizo, archivos modificados, costo en tokens. Los 3 más recientes se cargan al inicio. | ✅ Sí |
| `gotchas.md` | Trampas conocidas en esta codebase. Leer antes de ejecutar. | 🔶 Si es necesario |
| `memory/` | Hechos que persisten entre sesiones. | 🔶 Si es necesario |
| `agents/` | Overrides de agentes específicos del proyecto. | 🔶 Si es necesario |
| `skills/` | Overrides de skills específicas del proyecto. | 🔶 Si es necesario |
| `mcp.md` | Servidores MCP activos para este proyecto. | 🔶 Si es necesario |

---

## 🌐 Por qué agnóstico de IA

Claude Code lee `CLAUDE.md`. Gemini CLI lee `GEMINI.md`. Cursor lee `.cursorrules`. Cada tool tiene su propio archivo de entrada.

`.studio/` se ubica por debajo de todos ellos. Los archivos de entrada son wrappers delgados:

```markdown
# CLAUDE.md
@.studio/STUDIO.md
```

Cuando cambias de tool de IA, actualizas una línea. Tus estándares de engineering, decisiones tecnológicas y contexto del proyecto permanecen exactamente como estaban.

Los hooks y el dashboard están actualmente adaptados para Claude Code. La arquitectura está diseñada para adaptadores adicionales — ver `scripts/activate.py --tool=`.

---

## 💰 Costo en tokens

Cargar el contexto global completo al inicio de una sesión cuesta aproximadamente **8.000–10.000 tokens** — alrededor del 4–5% de una ventana de contexto de 200K.

El diseño mantiene esto bajo:
- Usando imperativos, no prosa — las reglas cargan rápido, las explicaciones no
- Cargando skills bajo demanda, no al inicio
- Limitando el changelog a los últimos 3 archivos
- Manteniendo `context.md` enfocado en el estado operativo, no en la documentación

---

## 🔄 El protocolo de sesión

Cada sesión sigue tres fases:

**▶ INICIO** — Cargar `tasks.md` + los 3 archivos `changelog/` más recientes. Cargar el modo de contexto (dev / research / review). Conocer el scope antes de tocar cualquier cosa.

**⚡ DURANTE** — Spec-first: ninguna nueva feature sin una spec aprobada. IGNORE.md: sin excepciones. Stack: seguir las decisiones, no explorar alternativas. Reglas: aplicadas por el modo de contexto.

**⏹ FIN** — Resumen, archivos modificados, costo en tokens. Entry del changelog escrita. Tasks actualizadas.

---

## 🏗️ Harness Engineering

Las cinco reglas en `harness.md` codifican lo que separa los sistemas IA en producción de las demos:

1. **🔷 Schema-first** — La salida del LLM validada con Pydantic o Zod antes de cualquier operación.
2. **🔷 Evals-driven** — Ningún prompt va a producción sin ejecutar contra un dataset golden.
3. **🔷 Context engineering** — El contenido crudo sin procesar nunca llega al LLM. Filtrar primero.
4. **🔷 Failure-aware design** — Exception chaining, retry con backoff, recuperación de resultados parciales.
5. **🔷 Observability** — Cada llamada al LLM registrada: modelo, tokens, latencia, costo.

---

## 🚀 Instalación

### 1. Instalar el studio global

```bash
git clone https://github.com/meowgl1/studio ~/.studio
pip install rich   # para el dashboard
```

### 2. Configurar para tu stack

```bash
# Editar decisiones tecnológicas
nano ~/.studio/stack.md

# Editar preferencias de comunicación
nano ~/.studio/persona.md
```

### 3. Activar los hooks (Claude Code)

```bash
python3 ~/.studio/scripts/activate.py

# Verificar estado
python3 ~/.studio/scripts/activate.py --status

# Eliminar hooks
python3 ~/.studio/scripts/activate.py --off
```

### 4. Conectar un proyecto

```bash
mkdir your-project/.studio

# Archivo de entrada — una línea
echo "@~/.studio/STUDIO.md" > your-project/.studio/STUDIO.md

# Entrada del proyecto para Claude Code — una línea
echo "@.studio/STUDIO.md" > your-project/CLAUDE.md

# Crear los archivos requeridos
touch your-project/.studio/context.md
touch your-project/.studio/tasks.md
mkdir your-project/.studio/changelog
```

Completa `context.md` con la arquitectura de tu proyecto, overrides del stack y restricciones.  
Completa `tasks.md` con los elementos del sprint actual.

### 5. Ejecutar el dashboard

```bash
# Desde el directorio de tu proyecto
python3 ~/.studio/scripts/dashboard.py

# O desde cualquier lugar
python3 ~/.studio/scripts/dashboard.py /path/to/project
```

---

## 💬 Opinión personal

Construí esto porque seguía perdiendo contexto.

Cada nueva sesión de Claude Code comenzaba desde cero. Re-explicaba el stack, re-establecía las restricciones, re-describía la arquitectura. La IA producía código técnicamente correcto que violaba decisiones que había tomado tres sesiones antes — no porque el modelo fuera malo, sino porque nunca le di la memoria que necesitaba para actuar de manera consistente.

El consejo estándar es "solo escribe un buen CLAUDE.md." Lo intenté. El problema es que un buen CLAUDE.md para un proyecto se convierte en un documento diferente de un buen CLAUDE.md para otro proyecto, y ninguno sobrevive los cambios de tool. Cada actualización era un impuesto.

`.studio` resuelve esto separando lo que es estable (estándares de engineering, decisiones tecnológicas, preferencias de comunicación) de lo que cambia (tareas actuales, sesiones recientes, estado del proyecto). Las partes estables viven globalmente y nunca necesitan ser reescritas.

Lo otro que estaba haciendo mal antes: pensaba que la IA necesitaba documentación. No es así. Necesita reglas. Las largas explicaciones sobre por qué usamos Pydantic son tokens desperdiciados. "SIEMPRE validar la salida del LLM con Pydantic antes de cualquier operación en DB" no lo es. El cambio de documentación a imperativos redujo el contexto de inicio de sesión en aproximadamente un 40% haciendo el comportamiento de la IA más consistente, no menos.

Este es un sistema vivo. Añado un gotcha cuando encuentro un bug recurrente. Añado un archivo de memoria cuando los agentes empiezan a perder estado importante. Añado una skill cuando me encuentro repitiendo la misma instrucción entre sesiones. El costo de mantenimiento es menor que el costo de no tenerlo.

---

## 📜 Licencia

MIT. Úsalo, adáptalo, rómpelo en piezas y toma lo que sea útil.
