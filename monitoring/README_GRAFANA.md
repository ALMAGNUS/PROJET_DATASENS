# Connexion Grafana – voir toutes les métriques et les courbes de drift

**Grafana et Prometheus ne démarrent pas tout seuls.** Si vous voyez « Ce site est inaccessible » ou `ERR_CONNECTION_REFUSED` sur http://localhost:3000, c’est que Grafana n’est pas lancé.

---

## Démarrer Grafana (Windows, le plus simple)

À la **racine du projet** (où se trouve `start_grafana.bat`) :

1. Double-cliquez sur **`start_grafana.bat`** (ou en ligne de commande : `start_grafana.bat`).
2. Attendez 5–10 secondes.
3. Ouvrez **http://localhost:3000** dans le navigateur.
4. Premier login : **admin** / **admin** (Grafana proposera de changer le mot de passe).

**Prérequis :** Docker doit être installé et en cours d’exécution. Si vous n’avez pas Docker, installez Grafana manuellement depuis https://grafana.com/grafana/download (Windows) et lancez Grafana, puis importez le dashboard comme indiqué plus bas.

---

## 1. Démarrer Prometheus (scrape l’API E2)

En local, utilisez la config qui pointe sur `localhost` :

```bash
# À la racine du projet
prometheus --config.file=monitoring/prometheus.local.yml --web.enable-lifecycle
```

Ou avec Docker :

```bash
docker run -d --name prometheus -p 9090:9090 \
  -v "%cd%\monitoring\prometheus.local.yml:/etc/prometheus/prometheus.yml" \
  prom/prometheus
```

Prometheus va scrapper :
- **localhost:8001** → API E2 (`/metrics`) : requêtes, latence, erreurs, auth, **drift**
- **localhost:8000** → Pipeline E1 (si le serveur métriques est lancé)

Vérifier : ouvrir http://localhost:9090 → Status → Targets. Les cibles `datasens-e2-api` doivent être "UP" si l’API tourne sur le port 8001.

---

## 2. Démarrer Grafana (rappel)

- **Avec le script :** à la racine du projet, lancer **`start_grafana.bat`** (voir section en haut du README).
- **En ligne de commande (Docker) :**
  ```bash
  docker run -d --name grafana -p 3000:3000 ^
    -v "%cd%\monitoring\grafana\provisioning:/etc/grafana/provisioning" ^
    -v "%cd%\monitoring\grafana\dashboards:/var/lib/grafana/dashboards" ^
    -e "GF_PATHS_PROVISIONING=/etc/grafana/provisioning" ^
    grafana/grafana
  ```

**Sans Docker** (Grafana installé sur la machine) :

1. Copier le contenu de `provisioning/datasources/` dans le répertoire de provisioning Grafana (datasource Prometheus → URL `http://localhost:9090`).
2. Importer le dashboard : **Dashboards** → **Import** → uploader `grafana/dashboards/datasens-full.json`.

---

## 3. Source de données Prometheus dans Grafana

- **Grafana sur la même machine que Prometheus** : URL = `http://localhost:9090`.
- **Grafana dans Docker, Prometheus sur l’hôte** : URL = `http://host.docker.internal:9090` (Windows/Mac).

Dans **Configuration** → **Data sources** → **Prometheus** : vérifier que l’URL est correcte et **Save & test**.

---

## 4. Dashboard « DataSens – Métriques & Drift »

Le dashboard `datasens-full.json` affiche :

- **Requêtes API** : total 24h, req/min, connexions actives, erreurs/min.
- **Requêtes par endpoint** et **Latence (p50, p95)**.
- **Authentifications** et **Accès par zone** (raw / silver / gold).
- **Drift** : entropy sentiment, dominance topic, score composite, nombre d’articles.
- **Courbes de drift** : évolution dans le temps (entropy, dominance, score).

Pour que les **courbes de drift** aient des points dans le temps, il faut mettre à jour les gauges régulièrement en appelant l’API :

```http
GET http://localhost:8001/api/v1/analytics/drift-metrics
```

(avec un token si l’API est protégée.)

Vous pouvez :
- Lancer cet appel depuis le **cockpit Streamlit** (bouton dédié dans Métriques avancées),
- Ou configurer un **cron / tâche planifiée** (ex. toutes les 5 min) qui appelle cette URL.

Après chaque appel, Prometheus récupère les nouvelles valeurs au prochain scrape (toutes les 10 s avec `prometheus.local.yml`), et Grafana affiche les courbes.

---

## 5. Résumé des URLs

| Service     | URL (local)        |
|------------|--------------------|
| API E2     | http://localhost:8001 |
| Métriques  | http://localhost:8001/metrics |
| Drift (mise à jour) | http://localhost:8001/api/v1/analytics/drift-metrics |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 (login admin / admin) |

Une fois Prometheus qui scrape l’API et Grafana connectée à Prometheus, toutes les métriques exposées (E2 + drift) sont visibles et les courbes de drift se remplissent à chaque appel à `/api/v1/analytics/drift-metrics`.
