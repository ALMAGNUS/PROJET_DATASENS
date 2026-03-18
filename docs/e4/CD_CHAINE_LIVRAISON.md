# Chaîne de livraison continue — DataSens E4

## Vue d'ensemble

La chaîne CD est définie dans `.github/workflows/ci-cd.yml`. Elle s'appuie sur la chaîne CI (tests) et ajoute le build Docker et le déploiement.

---

## Étapes et tâches

| Étape | Job | Description |
|-------|-----|-------------|
| 1. Test | `test` | Lint, pytest, validation structure |
| 2. Build | `build` | Build image Docker, push vers ghcr.io |
| 3. Deploy | `deploy` | Déploiement (placeholder, main uniquement) |

---

## Déclencheurs

- **Push** sur `main` ou `develop` : exécution complète
- **Pull request** : test + build (pas de push image si PR)
- **Deploy** : uniquement sur `main` après push

---

## Configuration

### Build Docker

- **Contexte** : racine du projet
- **Dockerfile** : `Dockerfile`
- **Registry** : `ghcr.io`
- **Tags** : branch, PR, semver, sha

### Permissions

- `contents: read` pour checkout
- `packages: write` pour push vers ghcr.io

---

## Packaging

L'image Docker inclut :

- Code source (src/, scripts/, etc.)
- Dépendances (requirements.txt)
- Configuration (sources_config.json, .env via variables)
- Commandes : `run_e2_api.py`, pipeline E1, etc.

---

## Procédure de livraison

1. **Développement** : commits sur `develop`, PR vers `main`
2. **Validation** : CI verte (tests, build)
3. **Merge** : PR mergée sur `main`
4. **Livraison** : workflow exécute deploy (placeholder : `echo "Deployment would happen here"`)
5. **Extension** : remplacer le placeholder par `docker-compose up -d` ou équivalent

---

## Versionnement

Les configurations sont dans `.github/workflows/ci-cd.yml` et versionnées avec le dépôt Git.
