# Accessibilité de la documentation — DataSens

**Critère C20/C18/C19** — Documentation dans un format respectant les recommandations d'accessibilité

---

## Référentiels

- **Association Valentin Haüy (AVH)** : [Accessibilité numérique](https://www.avh.asso.fr/nos-solutions/accessibilite/accessibilite-numerique)
- **Microsoft** : [Créer des documents Word accessibles](https://support.microsoft.com/fr-fr/office/rendre-vos-documents-word-accessible-9d5f4f26-7b6c-4a24-9a38-10a469c978f8)

---

## Format des documents

La documentation DataSens est rédigée en **Markdown** (`.md`), structurée pour être accessible :

| Critère | Application |
|---------|-------------|
| **Titres hiérarchiques** | `#`, `##`, `###` pour la structure (H1, H2, H3) |
| **Listes à puces / numérotées** | Pour les étapes et énumérations |
| **Tableaux** | En-têtes de colonnes explicites |
| **Texte alternatif** | Images : description en légende si nécessaire |
| **Contraste** | Texte lisible (fond clair/sombre selon thème) |

---

## Export pour accessibilité renforcée

Conformément aux recommandations AVH (format .docx privilégié au PDF pour l'accessibilité) :

1. **Markdown → Word** : `pandoc docs/METRIQUES_SEUILS_ALERTES.md -o docs/METRIQUES_SEUILS_ALERTES.docx`
2. **Markdown → PDF** : Exporter via Word ou outil respectant les balises de structure (signets, titres)
3. **Documents clés** : `METRIQUES_SEUILS_ALERTES.md`, `PROCEDURE_INCIDENTS.md`, `MONITORING_E2_API.md`, `README_E2_API.md` — exportables à la demande

---

## Vérification

- Les documents Markdown utilisent une structure de titres cohérente
- Les tableaux ont des en-têtes
- Les listes sont structurées (ul/ol)
- Pas d’information portée uniquement par la couleur ou l’image
