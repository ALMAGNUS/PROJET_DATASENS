"""Pages du cockpit DataSens (phase C, audit 2026-04).

Chaque onglet est dans son propre module et expose `render(ctx: PageContext)`.
Ordre d'orchestration dans src/streamlit/app.py :
    demo, overview, pipeline, flux, pilotage, ia, modeles, monitoring.
"""
