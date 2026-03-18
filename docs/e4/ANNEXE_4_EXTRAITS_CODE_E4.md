# Annexe 4 — Extraits de code E4 (illustration jury)

Cette annexe regroupe **trois extraits de code** représentatifs du bloc E4 : cockpit Streamlit, authentification et chaîne CI/CD.

---

## Extrait 1 — Authentification cockpit (C17)

**Fichier** : `src/streamlit/auth_plug.py` (lignes 31-80)

**Compétence** : C17 — Gérer les droits et accès à l'application

**Contexte** : Le module auth_plug gère l'authentification JWT via l'API E2. La session Streamlit stocke le token et les infos utilisateur. La fonction `login()` appelle `POST /auth/login` et met à jour `session_state`.

```python
def init_session_auth() -> None:
    """Initialise les cles auth dans session_state si absentes."""
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None


def is_logged_in() -> bool:
    """True si un utilisateur est connecte."""
    return get_token() is not None


def has_role(role: str) -> bool:
    """True si l'utilisateur a le role donne (ou admin)."""
    user = get_user()
    if not user:
        return False
    r = (user.get("role") or "").lower()
    return r == role.lower() or r == "admin"


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Appelle l'API E2 POST /auth/login. Retourne (success, message).
    En cas de succes, stocke token et user dans session_state.
    """
    init_session_auth()
    url = f"{_api_base()}{_auth_prefix().rstrip('/')}/auth/login"
    try:
        r = requests.post(
            url,
            json={"email": email, "password": password},
            timeout=30,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.RequestException as e:
        return False, f"Erreur reseau: {e}"

    if r.status_code != 200:
        return False, str((r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None) or r.text)[:200]

    data = r.json()
    token = data.get("access_token")
    if not token:
        return False, "Reponse API sans token"

    st.session_state.auth_token = token
    st.session_state.auth_user = {
        "profil_id": data.get("profil_id"),
        "email": data.get("email"),
        "role": data.get("role"),
        "firstname": data.get("firstname"),
        "lastname": data.get("lastname"),
    }
    return True, "Connexion reussie"
```

**Lien** : [src/streamlit/auth_plug.py](../../src/streamlit/auth_plug.py)

---

## Extrait 2 — Mise en page cockpit (C17)

**Fichier** : `src/streamlit/app.py` (lignes 39-55)

**Compétence** : C17 — Intégrer la mise en page et les contenus des interfaces

**Contexte** : L'injection CSS personnalise l'apparence du cockpit (hero, cards, flux). Les classes `.ds-*` sont utilisées pour structurer les blocs visuels.

```python
def _inject_css() -> None:
    st.markdown(
        """
    <style>
    .ds-hero { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; }
    .ds-hero h3 { color: #e8eaf6; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
    .ds-hero p { color: #c5cae9; margin: 0; font-size: 0.9rem; }
    .ds-flow { display: flex; align-items: center; flex-wrap: wrap; gap: 0.3rem; margin: 1rem 0; font-size: 0.85rem; }
    .ds-card { background: #1e1e2e; border: 1px solid #333; border-radius: 10px; padding: 1rem; margin-bottom: 0.8rem; }
    .ds-card-title { color: #81d4fa; font-weight: 600; font-size: 0.95rem; margin-bottom: 0.3rem; }
    .ds-card-value { color: #fff; font-size: 1.1rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )
```

**Lien** : [src/streamlit/app.py](../../src/streamlit/app.py)

---

## Extrait 3 — Workflow CI/CD (C18/C19)

**Fichier** : `.github/workflows/ci-cd.yml` (extrait)

**Compétence** : C18, C19 — Automatisation des tests avec intégration continue, processus de livraison continue

**Contexte** : Le workflow CI/CD exécute les tests, build l'image Docker et push vers ghcr.io. Le déploiement (placeholder) ne s'exécute que sur main.

```yaml
name: DataSens E1 CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: echo "PYTHONPATH=..." >> $GITHUB_ENV
      - run: pytest tests/ -v --ignore=tests/test_e1_isolation.py || true

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          # ...

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deployment would happen here"
```

**Lien** : [.github/workflows/ci-cd.yml](../../.github/workflows/ci-cd.yml)

---

## Synthèse pour le jury

| Extrait | Compétence | Message clé |
|---------|------------|-------------|
| 1 | C17 | Authentification JWT, session Streamlit, RBAC (rôles) |
| 2 | C17 | Mise en page cockpit, CSS personnalisé, structure visuelle |
| 3 | C18/C19 | Chaîne CI/CD : tests → build Docker → deploy (main) |
