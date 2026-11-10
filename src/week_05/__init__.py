"""Vetology Week 5 — independent rebuild of the canine thorax evaluation app.

The package classifies 20 canine thoracic conditions from original radiologist
report text with OpenAI (via LangChain) using the unchanged Canine Thorax Master
Prompt V1.3, and evaluates predictions in two strictly separate workflows:

* Matrix 1 — Original Vetology scoring vs. LLM predictions.
* Matrix 2 — Gold Standard scoring vs. LLM predictions.

This package does not import or modify the Week 4 implementation.
"""

__all__ = ["__version__"]

__version__ = "5.0.0"
