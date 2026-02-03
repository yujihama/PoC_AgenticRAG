"""
Hypothesis-Driven Audit Agent Architecture

This module implements a multi-agent pattern for complex audit tasks:
- SupervisorAgent: Orchestrates specialist agents and aggregates results
- HypothesisAgent: Generates hypotheses about potential discrepancies
- VerifierAgent: Verifies hypotheses against evidence and domain knowledge
"""

from agents.base_agent import BaseSpecialistAgent
from agents.hypothesis_agent import HypothesisAgent
from agents.verifier_agent import VerifierAgent
from agents.supervisor_agent import SupervisorAgent

__all__ = [
    "BaseSpecialistAgent",
    "HypothesisAgent",
    "VerifierAgent",
    "SupervisorAgent",
]
