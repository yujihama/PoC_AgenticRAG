"""Hypothesis generation agent for audit tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import AgentResult, BaseSpecialistAgent


@dataclass
class Hypothesis:
    """A single hypothesis about a potential discrepancy."""

    id: str
    description: str
    category: str  # "pricing", "quantity", "timing", "vendor", "compliance", etc.
    severity: str  # "high", "medium", "low"
    evidence_needed: list[str] = field(default_factory=list)
    initial_confidence: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "evidence_needed": self.evidence_needed,
            "initial_confidence": self.initial_confidence,
        }


class HypothesisAgent(BaseSpecialistAgent):
    """
    Specialist agent for generating hypotheses about potential discrepancies.

    This agent analyzes transaction data and documents to proactively generate
    hypotheses about potential issues that should be investigated. It implements
    divergent thinking to identify multiple possible explanations for discrepancies.
    """

    SYSTEM_PROMPT = """あなたは監査仮説生成の専門エージェントです。
取引データや文書を分析し、潜在的な問題点についての仮説を生成することが役割です。

仮説生成の原則:
1. 多角的視点: 価格、数量、タイミング、ベンダー、コンプライアンスなど複数の観点から検討
2. 根拠に基づく推論: 提供されたデータから論理的に導出される仮説のみを提案
3. 重要度の評価: 各仮説のビジネスインパクトに基づいて重要度を評価
4. 検証可能性: 各仮説について必要な証拠を明示

出力形式（JSON）:
{
    "hypotheses": [
        {
            "id": "H001",
            "description": "仮説の詳細な説明",
            "category": "pricing|quantity|timing|vendor|compliance|other",
            "severity": "high|medium|low",
            "evidence_needed": ["必要な証拠1", "必要な証拠2"],
            "initial_confidence": 0.0-1.0
        }
    ],
    "reasoning": "仮説生成の思考過程",
    "areas_not_covered": ["カバーできなかった領域があれば"]
}"""

    def __init__(
        self,
        model: BaseChatModel,
        max_iterations: int = 3,
    ):
        super().__init__(
            name="hypothesis_generator",
            model=model,
            description="Generate hypotheses about potential discrepancies in audit data",
            max_iterations=max_iterations,
        )

    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """
        Generate hypotheses based on the provided task and context.

        Args:
            task: Description of what to analyze
            context: Should contain 'documents' and optionally 'transaction_data'

        Returns:
            AgentResult containing list of Hypothesis objects
        """
        context = context or {}

        # Build the prompt with context
        prompt_parts = [f"分析対象: {task}\n"]

        if "documents" in context:
            prompt_parts.append(f"関連文書:\n{context['documents']}\n")

        if "transaction_data" in context:
            prompt_parts.append(f"取引データ:\n{context['transaction_data']}\n")

        if "previous_findings" in context:
            prompt_parts.append(f"過去の発見事項:\n{context['previous_findings']}\n")

        prompt_parts.append(
            "\n上記の情報を分析し、潜在的な問題についての仮説を生成してください。"
            "JSON形式で出力してください。"
        )

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content="\n".join(prompt_parts)),
        ]

        try:
            response = self.model.invoke(messages)
            content = response.content

            # Parse the JSON response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result_data = json.loads(content.strip())

            hypotheses = [
                Hypothesis(
                    id=h.get("id", f"H{i:03d}"),
                    description=h.get("description", ""),
                    category=h.get("category", "other"),
                    severity=h.get("severity", "medium"),
                    evidence_needed=h.get("evidence_needed", []),
                    initial_confidence=h.get("initial_confidence", 0.5),
                )
                for i, h in enumerate(result_data.get("hypotheses", []), 1)
            ]

            # Store in memory
            self.add_to_memory({
                "task": task,
                "hypotheses_count": len(hypotheses),
                "categories": list(set(h.category for h in hypotheses)),
            })

            return AgentResult(
                agent_name=self.name,
                status="success",
                data=[h.to_dict() for h in hypotheses],
                confidence=0.8 if hypotheses else 0.3,
                reasoning=result_data.get("reasoning", ""),
                metadata={
                    "areas_not_covered": result_data.get("areas_not_covered", []),
                    "hypothesis_count": len(hypotheses),
                },
            )

        except json.JSONDecodeError as e:
            return AgentResult(
                agent_name=self.name,
                status="partial",
                data=[],
                confidence=0.2,
                reasoning=f"JSON解析エラー: {e}. 生の応答: {content[:500]}",
                metadata={"error": str(e)},
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                status="failed",
                data=[],
                confidence=0.0,
                reasoning=f"仮説生成中にエラーが発生: {e}",
                metadata={"error": str(e)},
            )
