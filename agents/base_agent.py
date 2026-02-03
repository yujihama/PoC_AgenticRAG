"""Base specialist agent class for the multi-agent architecture."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel


@dataclass
class AgentResult:
    """Result returned by specialist agents."""

    agent_name: str
    status: str  # "success", "partial", "failed"
    data: Any
    confidence: float = 0.0  # 0.0 to 1.0
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "data": self.data,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }


class BaseSpecialistAgent(ABC):
    """
    Base class for specialist agents in the multi-agent architecture.

    Specialist agents can be wrapped as tools and invoked by the supervisor agent.
    This implements the "Agent-as-a-Tool" pattern compatible with LangChain v1+.
    """

    def __init__(
        self,
        name: str,
        model: BaseChatModel,
        description: str = "",
        max_iterations: int = 5,
    ):
        self.name = name
        self.model = model
        self.description = description
        self.max_iterations = max_iterations
        self._memory: list[dict[str, Any]] = []

    @abstractmethod
    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """
        Execute the agent's primary task.

        Args:
            task: The task description or query
            context: Optional context from supervisor or previous agents

        Returns:
            AgentResult with the agent's output
        """
        pass

    def add_to_memory(self, entry: dict[str, Any]) -> None:
        """Add an entry to the agent's working memory."""
        self._memory.append(entry)

    def get_memory(self) -> list[dict[str, Any]]:
        """Get the agent's working memory."""
        return self._memory.copy()

    def clear_memory(self) -> None:
        """Clear the agent's working memory."""
        self._memory.clear()

    def as_tool_description(self) -> str:
        """Return a description suitable for tool registration."""
        return self.description or f"Invoke the {self.name} specialist agent"
