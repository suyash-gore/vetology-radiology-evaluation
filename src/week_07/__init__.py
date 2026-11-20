"""Vetology Week 7 — independent Google Gemini evaluation pipeline.

Reproduces the Week 5 Matrix 1 (original Vetology scores) and Matrix 2 (Gold
Standard) workflows with ``gemini-3.8-flash`` and adds an offline comparison of
the saved Week 5 OpenAI predictions with the Week 7 Gemini predictions.

Week 7 never imports ``week_05`` or ``week_04`` at runtime (only parity tests
do) and never writes outside ``outputs/week_07/``.
"""
