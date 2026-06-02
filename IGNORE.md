# IGNORE — Never touch

## Secrets
.env | .env.* | .env.local | .env.production | *.pem | *.key | secrets/

## Version control
.git/ | .github/ | .gitignore

## Build artifacts
.next/ | dist/ | build/ | __pycache__/ | *.pyc | .cache/

## Dependencies
node_modules/ | .venv/ | venv/

## System
.DS_Store | Thumbs.db

## CI/CD
.github/workflows/ | Dockerfile (senza approvazione esplicita)

## Database
migrations/ (leggere sì, modificare solo con conferma esplicita)

## Personal files
.obsidian/ | .vscode/ | persona.md