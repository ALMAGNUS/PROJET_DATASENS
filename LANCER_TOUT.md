# DataSens – Tout lancer dans le bon ordre

Toutes les commandes à exécuter **dans l’ordre**. À faire depuis la **racine du projet** (dossier contenant `main.py`, `start_full.bat`, etc.).

---

## Ce qui demande Docker

- **Grafana** (tableaux de bord, courbes de drift) → besoin de **Docker**.
- **Prometheus** (récupère les métriques pour Grafana) → possible **avec Docker** ou **sans** (exe téléchargé).

Si vous n’avez pas Docker : vous pouvez quand même lancer le **cockpit**, l’**API** et le **pipeline** (tout sauf Grafana / Prometheus).

---

## Ordre recommandé

### 1. Activer l’environnement Python (dans chaque terminal où vous lancez des commandes)

```bat
cd /d "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"
.venv\Scripts\activate.bat
```

*(Une seule fois par terminal. Si vous utilisez uniquement les `.bat` ci‑dessous, ils font le `cd` et l’activation pour vous.)*

---

### 2. [Optionnel] Démarrer Prometheus (pour les métriques / Grafana)

**A. Avec Docker (si installé) :**

```bat
docker run -d --name prometheus -p 9090:9090 -v "%cd%\monitoring\prometheus.local.yml:/etc/prometheus/prometheus.yml" prom/prometheus
```

**B. Sans Docker** (après avoir téléchargé Prometheus et ajouté au PATH) :

```bat
start_prometheus.bat
```

Ou à la main :

```bat
prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
```

→ Prometheus : http://localhost:9090

---

### 3. [Optionnel] Démarrer Grafana (nécessite Docker)

```bat
start_grafana.bat
```

Ou à la main :

```bat
docker run -d --name grafana -p 3000:3000 -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" grafana/grafana
```

Attendre 5–10 s puis ouvrir : http://localhost:3000 (login : **admin** / **admin**).

---

### 4. Démarrer l’API E2 (Backend)

**Dans un premier terminal :**

```bat
cd /d "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"
.venv\Scripts\activate.bat
python run_e2_api.py
```

Ou double‑cliquer sur un script qui fait ça (voir **Script unique** plus bas).

→ API : http://localhost:8001 (ne pas fermer ce terminal).

---

### 5. Démarrer le Cockpit Streamlit (Frontend)

**Dans un second terminal :**

```bat
cd /d "C:\Users\Utilisateur\Desktop\DEV IA 2025\PROJET_DATASENS"
.venv\Scripts\activate.bat
streamlit run src\streamlit\app.py
```

Ou double‑cliquer sur :

```bat
start_cockpit.bat
```

→ Cockpit : http://localhost:8501 (ne pas fermer ce terminal).

---

### 6. [Optionnel] Lancer le pipeline E1 depuis le cockpit

Une fois le cockpit ouvert : onglet **Pilotage** → bouton **Lancer pipeline (main.py)**. Pas de commande à taper.

---

## Résumé des URLs

| Service    | URL                  | Comment le lancer                          |
|-----------|----------------------|--------------------------------------------|
| Cockpit   | http://localhost:8501 | `start_cockpit.bat` ou `streamlit run src\streamlit\app.py` |
| API E2    | http://localhost:8001 | `python run_e2_api.py` (terminal dédié)     |
| Prometheus| http://localhost:9090 | `start_prometheus.bat` ou Docker (voir 2)  |
| Grafana   | http://localhost:3000 | `start_grafana.bat` (Docker requis)        |

---

## Script unique : tout lancer d’un coup

Double‑cliquer sur :

```bat
lancer_tout.bat
```

Ce script (à la racine du projet) :

1. Démarre Prometheus avec Docker (si Docker est installé).
2. Démarre Grafana avec Docker (si Docker est installé).
3. Ouvre un terminal avec l’API E2 (`python run_e2_api.py`).
4. Attend quelques secondes.
5. Ouvre un terminal avec le Cockpit (`streamlit run src\streamlit\app.py`).

Vous n’avez plus qu’à laisser les deux terminaux ouverts et à ouvrir http://localhost:8501 (cockpit) et, si vous avez lancé Grafana, http://localhost:3000 (Grafana).
