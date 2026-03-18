# Objectifs d'accessibilité — DataSens E4

## Référentiels

- **WCAG 2.1** (Web Content Accessibility Guidelines) — niveau AA
- **RG2AA** (Référentiel général d'amélioration de l'accessibilité)
- **Association Valentin Haüy (AVH)** — recommandations accessibilité numérique
- **Microsoft** — documents accessibles (Word, PDF)

---

## Objectifs techniques

| Critère | Objectif | Application DataSens |
|---------|----------|----------------------|
| **1.1 Texte alternatif** | Tout contenu non textuel a une alternative | Images : légendes, descriptions dans la doc |
| **1.3 Adaptable** | Contenu structuré (titres, listes) | Markdown : H1/H2/H3, listes, tableaux |
| **2.1 Clavier** | Toutes les fonctionnalités accessibles au clavier | Streamlit : navigation native clavier |
| **2.4 Navigable** | Titres, ordre de tabulation logique | Structure des pages, sidebar |
| **2.5 Entrées** | Alternatives aux gestes complexes | Formulaires, boutons |
| **3.1 Lisible** | Langue identifiable | `lang="fr"` sur les pages |
| **4.1 Compatible** | Structure sémantique | HTML généré par Streamlit, balises appropriées |

---

## Critères dans les user stories

Les user stories prioritaires incluent des critères d'accessibilité dans leur définition de fait :

- **US cockpit** : « L'interface respecte une structure de titres H1/H2/H3 »
- **US documentation** : « Les tableaux ont des en-têtes explicites »
- **US export** : « Les documents exportés (PDF/Word) sont structurés pour lecteurs d'écran »

---

## Documentation

La documentation technique est rédigée en Markdown avec :

- Titres hiérarchiques cohérents
- Tableaux avec en-têtes
- Listes structurées
- Pas d'information portée uniquement par la couleur

Export accessible : `pandoc doc.md -o doc.docx` (format privilégié AVH).

Voir aussi : `docs/ACCESSIBILITE_DOCUMENTATION.md`.
