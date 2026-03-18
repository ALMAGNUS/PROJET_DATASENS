# 🎯 Setup GitHub Projects pour DataSens E1

## 📋 Étape 1 : Créer le Project

1. Aller sur votre repo GitHub : `https://github.com/ALMAGNUS/PROJET_DATASENS`
2. Cliquer sur **"Projects"** (onglet en haut)
3. Cliquer sur **"New project"**
4. Choisir **"Board"** (template Kanban)
5. Nom : **"DataSens E1 - Sprint Backlog"**

---

## 📊 Étape 2 : Configurer les Colonnes

### Colonnes Kanban :
1. **Backlog** - User Stories non planifiées
2. **To Do** - User Stories du sprint actuel
3. **In Progress** - En cours de développement
4. **Review** - Code review / Tests
5. **Done** - Complétées et validées

---

## 🏷️ Étape 3 : Créer les Labels (Epics)

### Labels à créer :
- `epic:collecte` - EPIC 1 : Pipeline de Collecte
- `epic:enrichissement` - EPIC 2 : Enrichissement IA
- `epic:exports` - EPIC 3 : Exports et Partitionnement
- `epic:monitoring` - EPIC 4 : Monitoring et Observabilité
- `epic:docker` - EPIC 5 : Containerisation
- `epic:zzdb` - EPIC 6 : Données Synthétiques

### Labels de statut :
- `status:done` - Complété
- `status:in-progress` - En cours
- `status:blocked` - Bloqué
- `status:review` - En review

### Labels de priorité :
- `priority:high` - Haute priorité
- `priority:medium` - Priorité moyenne
- `priority:low` - Basse priorité

---

## 📝 Étape 4 : Créer les Issues (User Stories)

### Template Issue :

```markdown
## User Story

**US-XX.X : [Titre]**

En tant que [Persona]
Je veux [Action]
Afin de [Bénéfice]

## Critères d'acceptation
- [ ] Critère 1
- [ ] Critère 2
- [ ] Critère 3

## Définition de Fait
- [ ] Code review OK
- [ ] Tests passent
- [ ] Documentation à jour
- [ ] Déployé

## Estimation
[X] points

## Epic
[EPIC X]
```

### Exemple Issue :

**Titre** : `US-1.1 : Extraire des données depuis RSS, API, Web Scraping`

**Labels** : `epic:collecte`, `priority:high`, `status:done`

**Description** :
```markdown
En tant que **Développeur Backend**
Je veux **extraire des données depuis RSS, API, Web Scraping**
Afin de **collecter des articles français pour l'analyse de sentiment**

## Critères d'acceptation
- [x] RSSExtractor fonctionnel
- [x] APIExtractor fonctionnel
- [x] ScrapingExtractor fonctionnel
- [x] Factory create_extractor() route correctement

## Définition de Fait
- [x] Code review OK
- [x] Tests passent
- [x] Documentation à jour
- [x] Déployé

## Estimation
5 points

## Epic
EPIC 1 : Pipeline de Collecte
```

---

## 🎯 Étape 5 : Créer les Milestones (Sprints)

### Milestones à créer :

1. **Sprint 0 : Fondations** (✅ COMPLÉTÉ)
   - Date : [Date début] - [Date fin]
   - Issues : US-1.1 à US-1.5

2. **Sprint 1 : Enrichissement** (✅ COMPLÉTÉ)
   - Issues : US-2.1 à US-2.4

3. **Sprint 2 : Exports** (✅ COMPLÉTÉ)
   - Issues : US-3.1 à US-3.4

4. **Sprint 3 : Monitoring** (✅ COMPLÉTÉ)
   - Issues : US-4.1 à US-4.4

5. **Sprint 4 : Docker** (✅ COMPLÉTÉ)
   - Issues : US-5.1 à US-5.4

6. **Sprint 5 : ZZDB** (✅ COMPLÉTÉ)
   - Issues : US-6.1 à US-6.5

7. **Sprint 6 : Performance** (🔄 FUTUR)
   - Issues : US-7.1 à US-7.3

---

## 🔄 Workflow GitHub Projects

### 1. **Créer Issue**
- Titre : `US-X.X : [Description]`
- Labels : Epic + Priorité
- Milestone : Sprint correspondant
- Assigné à : Vous-même

### 2. **Développer**
- Créer branche : `feature/US-X.X-description`
- Commits : `fix: US-X.X - [description]`
- PR : `feat: US-X.X - [description]`

### 3. **Déplacer dans Kanban**
- **Backlog** → **To Do** (planification sprint)
- **To Do** → **In Progress** (début développement)
- **In Progress** → **Review** (PR créée)
- **Review** → **Done** (PR mergée)

### 4. **Fermer Issue**
- Quand PR mergée, fermer l'issue
- Issue reste dans "Done" pour historique

---

## 📊 Vues Utiles

### **Vue Kanban** (Par défaut)
- Colonnes : Backlog | To Do | In Progress | Review | Done
- Filtres : Par Epic, Par Sprint, Par Assigné

### **Vue Table** (Alternative)
- Colonnes : Titre | Epic | Sprint | Statut | Assigné | Estimation
- Tri : Par priorité, par sprint

---

## 🎯 Automatisation (Optionnel)

### **Actions GitHub** (`.github/workflows/project-automation.yml`) :

```yaml
name: Project Automation
on:
  issues:
    types: [opened, closed]
  pull_request:
    types: [opened, closed, merged]

jobs:
  update-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v0.4.0
        with:
          project-url: ${{ secrets.PROJECT_URL }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## 📈 Métriques à Suivre

### **Par Sprint** :
- Vélocité (points complétés)
- Burndown (points restants)
- Issues complétées
- Temps moyen par US

### **Par Epic** :
- Progression (% complété)
- Issues restantes
- Blocages

---

## ✅ Checklist Setup

- [ ] Project créé
- [ ] Colonnes configurées
- [ ] Labels créés (Epics + Statuts + Priorités)
- [ ] Milestones créés (Sprints)
- [ ] Issues créées (User Stories)
- [ ] Issues assignées aux Sprints
- [ ] Issues labellisées (Epics)
- [ ] Workflow testé (Backlog → Done)

---

## 🚀 Quick Start

1. **Créer Project** : `Settings > Projects > New Project > Board`
2. **Créer Labels** : `Issues > Labels > New label`
3. **Créer Milestones** : `Issues > Milestones > New milestone`
4. **Créer Issues** : `Issues > New issue` (utiliser template)
5. **Déplacer dans Kanban** : Drag & drop

---

## 📚 Ressources

- **GitHub Projects Docs** : https://docs.github.com/en/issues/planning-and-tracking-work-with-project-boards
- **GitHub Issues Templates** : https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests
