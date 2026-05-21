**Structure du projet :**

```
docker-compose-app/
├── .env
├── .gitignore
├── README.md
├── docker-compose.yml
│
├── fastapi_app/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── streamlit_app/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── prometheus/
│   └── prometheus.yml
│
├── grafana/
│   ├── dashboards.py
│   │   ├── dashboards.json
│   │   └── dashboards.yml
└── └── datasources
        └── datasources.yml
```

**Fichier `.env` :**

```
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
FASTAPI_PORT=8080
STREAMLIT_PORT=8501
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```


**FastAPI (`fastapi_app/requirements.txt`) :**

```
fastapi
uvicorn
pydantic
prometheus-client
python-multipart
```

**Streamlit (`streamlit_app/requirements.txt`) :**

```
streamlit
requests
loguru
```

---

# M5 Brief 3 — Monitoring d'une stack IA conteneurisée

Stack complète FastAPI + Streamlit avec supervision Prometheus / Grafana / Uptime Kuma et alertes Discord + ntfy.

## Architecture

```
Streamlit ──▶ FastAPI ──┬──▶ /metrics ──▶ Prometheus ──▶ Grafana (1860)
                        │
                        └──▶ /health ──▶ Uptime Kuma ──▶ Discord + ntfy
                                                          (en cas de down)
Node Exporter ──▶ métriques système ──▶ Prometheus ──▶ Grafana (1860)
```

## Services et ports

| Service       | URL                     | Rôle                                          |
|---------------|-------------------------|-----------------------------------------------|
| Streamlit     | http://localhost:8501   | Frontend qui envoie une couleur à l'API       |
| FastAPI       | http://localhost:8080   | API métier ; expose `/health` et `/metrics`   |
| Prometheus    | http://localhost:9090   | Collecte des métriques                        |
| Grafana       | http://localhost:3000   | Visualisation (login: admin / admin)          |
| Uptime Kuma   | http://localhost:3001   | Monitoring d'accessibilité de l'API           |
| Node Exporter | (interne, port 9100)    | Métriques système pour le dashboard 1860      |

## Lancement

```bash
# Récupérer le dashboard Grafana 1860
mkdir -p grafana/provisioning/dashboards
curl -L "https://grafana.com/api/dashboards/1860/revisions/latest/download" \
  -o grafana/provisioning/dashboards/dashboard.json

# Nettoyer le JSON (DS_PROMETHEUS → Prometheus, suppression __inputs)
python3 -c "
import json
with open('grafana/provisioning/dashboards/dashboard.json') as f:
    d = json.load(f)
d.pop('__inputs', None); d.pop('__requires', None)
s = json.dumps(d).replace('\${DS_PROMETHEUS}', 'Prometheus')
with open('grafana/provisioning/dashboards/dashboard.json', 'w') as f:
    f.write(s)
"

# Démarrer toute la stack
docker compose up -d --build

# Suivre les logs
docker compose logs -f
```

## Vérifications

### 1. FastAPI répond

```bash
curl http://localhost:8080/health
# {"status":"ok"}

curl http://localhost:8080/metrics | head -20
# # HELP http_requests_total Nombre total de requêtes HTTP reçues
# # TYPE http_requests_total counter
# ...
```

### 2. Prometheus scrape bien les 3 jobs

Va sur http://localhost:9090/targets, vérifie que les 3 endpoints sont **UP** :
- `prometheus` (localhost:9090)
- `fastapi` (api:8080)
- `node` (node-exporter:9100)

### 3. Grafana affiche le dashboard 1860

Va sur http://localhost:3000 (admin/admin) → **Dashboards** → tu dois voir **"Node Exporter Full"** automatiquement importé.

### 4. Uptime Kuma surveille l'API

Va sur http://localhost:3001, configure (première fois) :
- Crée le compte admin
- Add New Monitor → HTTP(s) → URL `http://api:8080/health` → interval 60s

### 5. Test d'alerte Discord (et ntfy)

```bash
# Stoppe l'API → dans ~2 minutes les notifs partent
docker compose stop api

# Vérifier que Discord + ntfy reçoivent le message "DOWN"
# Puis remettre en marche
docker compose start api

# ~1 minute plus tard, notification "UP" envoyée
```

## Configuration Discord webhook

1. Créer un serveur Discord (gratuit, en 20 secondes)
2. Paramètres d'un salon → Intégrations → Créer un webhook
3. Copier l'URL
4. Dans Uptime Kuma : Settings → Notifications → Setup Notification → Discord
5. Coller l'URL, tester, sauvegarder

## Configuration ntfy (bonus)

Dans Uptime Kuma : Settings → Notifications → Setup Notification → Ntfy
- Server URL : ton instance ntfy
- Topic : `fastia-alerts`
- Priority : 4 (high)

## Volumes persistants

- `prometheus_data` : historique des métriques
- `grafana_data` : config Grafana (dashboards customs)
- `uptime_kuma_data` : config et historique Uptime Kuma

Pour tout réinitialiser : `docker compose down -v` (le `-v` supprime aussi les volumes).

## Pourquoi cette stack

| Outil         | Question répondue                              |
|---------------|------------------------------------------------|
| Prometheus    | "Quel est l'état du système ?" (métriques)     |
| Grafana       | "Comment ça évolue dans le temps ?" (visu)     |
| Node Exporter | "Métriques bas-niveau de la machine"           |
| Uptime Kuma   | "Le service est-il joignable ?" (oui/non)      |
| Discord/ntfy  | "Alerter un humain en cas de panne"            |

Démarche MLOps : on observe le système (Prometheus), on visualise les tendances (Grafana), on alerte sur les pannes (Uptime Kuma + webhooks). Aucune panne ne passe inaperçue.