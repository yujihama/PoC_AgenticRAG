"""Supervisor agent that orchestrates specialist agents for audit tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.language_models import BaseChatModel

from agents.base_agent import AgentResult, BaseSpecialistAgent
from agents.hypothesis_agent import HypothesisAgent
from agents.verifier_agent import VerifierAgent


@dataclass
class AuditReport:
    """Final audit report aggregating all agent findings."""

    transaction_id: str
    summary: str
    confirmed_issues: list[dict[str, Any]] = field(default_factory=list)
    potential_issues: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    agent_contributions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "summary": self.summary,
            "confirmed_issues": self.confirmed_issues,
            "potential_issues": self.potential_issues,
            "recommendations": self.recommendations,
            "confidence_score": self.confidence_score,
            "agent_contributions": self.agent_contributions,
        }


class SupervisorAgent:
    """
    Supervisor agent that orchestrates specialist agents for complex audit tasks.

    This implements the "Agent-as-a-Tool" pattern where specialist agents are
    wrapped as callable tools that the supervisor can invoke alongside traditional
    tools like document search and data extraction.
    """

    SYSTEM_PROMPT = """あなたは監査タスクを統括するスーパーバイザーエージェントです。
複雑な監査タスクを効率的に完了するために、専門エージェントとツールを適切に活用してください。

利用可能な専門エージェント:
1. generate_hypotheses: 仮説生成エージェント - 取引データの潜在的な問題についての仮説を生成
2. verify_hypotheses: 仮説検証エージェント - 生成された仮説を証拠に基づいて検証

監査プロセス:
1. 関連文書とデータを収集（search_all_files, extract_data）
2. ドメイン知識を参照（lookup_knowledge）
3. 仮説を生成（generate_hypotheses）
4. 仮説を検証（verify_hypotheses）
5. 結果を集約してレポートを作成

重要な原則:
- 各ステップの根拠を明確に記録する
- 専門エージェントの出力を批判的に評価する
- 信頼度スコアを考慮して判断する
- 不確実な場合は追加調査を提案する

最終回答では、発見された問題、その根拠、推奨アクションを明確に示してください。"""

    def __init__(
        self,
        model: BaseChatModel,
        base_tools: list[Callable] | None = None,
        knowledge_lookup_fn: Callable[[str, str], str] | None = None,
        extract_data_fn: Callable[[str, str], str] | None = None,
        analyze_data_fn: Callable[[str, str, str], str] | None = None,
    ):
        """
        Initialize the supervisor agent.

        Args:
            model: The LLM to use for the supervisor
            base_tools: Base tools like search_file, read_file, etc.
            knowledge_lookup_fn: Function to lookup domain knowledge
            extract_data_fn: Function to extract data from documents
            analyze_data_fn: Function to analyze data
        """
        self.model = model
        self.base_tools = base_tools or []

        # Initialize specialist agents
        self.hypothesis_agent = HypothesisAgent(model=model)
        self.verifier_agent = VerifierAgent(model=model)

        # Store function references for tool creation
        self._knowledge_lookup_fn = knowledge_lookup_fn
        self._extract_data_fn = extract_data_fn
        self._analyze_data_fn = analyze_data_fn

        # Shared context between agents
        self._shared_context: dict[str, Any] = {}

        # Build the agent with all tools
        self._agent = self._build_agent()

    def _build_agent(self):
        """Build the LangChain agent with specialist agent tools."""
        # Create tools that wrap specialist agents
        specialist_tools = self._create_specialist_tools()

        # Create parameterized tools
        parameterized_tools = self._create_parameterized_tools()

        # Combine all tools
        all_tools = list(self.base_tools) + specialist_tools + parameterized_tools

        return create_agent(
            model=self.model,
            tools=all_tools,
            system_prompt=self.SYSTEM_PROMPT,
        )

    def _create_specialist_tools(self) -> list[Callable]:
        """Create tools that wrap specialist agents."""
        # Capture self for closure
        supervisor = self

        @tool
        def generate_hypotheses(task: str, documents: str = "", transaction_data: str = "") -> str:
            """
            仮説生成エージェントを呼び出して、取引データの潜在的な問題についての仮説を生成します。

            Args:
                task: 分析対象の説明
                documents: 関連する文書内容
                transaction_data: 取引データ

            Returns:
                生成された仮説のJSON文字列
            """
            context = {
                "documents": documents or supervisor._shared_context.get("documents", ""),
                "transaction_data": transaction_data
                or supervisor._shared_context.get("transaction_data", ""),
            }

            result = supervisor.hypothesis_agent.run(task, context)

            # Store results in shared context
            supervisor._shared_context["hypotheses"] = result.data
            supervisor._shared_context["hypothesis_reasoning"] = result.reasoning

            return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

        @tool
        def verify_hypotheses(
            task: str, hypotheses: str = "", evidence: str = "", domain_knowledge: str = ""
        ) -> str:
            """
            仮説検証エージェントを呼び出して、仮説を証拠に基づいて検証します。

            Args:
                task: 検証タスクの説明
                hypotheses: 検証対象の仮説（JSON形式）。省略時は前回生成された仮説を使用
                evidence: 利用可能な証拠
                domain_knowledge: ドメイン知識

            Returns:
                検証結果のJSON文字列
            """
            # Parse hypotheses if provided as string
            if hypotheses:
                try:
                    hypotheses_data = json.loads(hypotheses)
                except json.JSONDecodeError:
                    hypotheses_data = hypotheses
            else:
                hypotheses_data = supervisor._shared_context.get("hypotheses", [])

            context = {
                "hypotheses": hypotheses_data,
                "evidence": evidence or supervisor._shared_context.get("evidence", ""),
                "domain_knowledge": domain_knowledge
                or supervisor._shared_context.get("domain_knowledge", ""),
            }

            result = supervisor.verifier_agent.run(task, context)

            # Store results in shared context
            supervisor._shared_context["verifications"] = result.data
            supervisor._shared_context["verification_reasoning"] = result.reasoning

            return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

        return [generate_hypotheses, verify_hypotheses]

    def _create_parameterized_tools(self) -> list[Callable]:
        """Create parameterized tools for data extraction and analysis."""
        supervisor = self

        @tool
        def extract_data(source: str, extraction_type: str) -> str:
            """
            文書やデータソースから情報を抽出します。

            Args:
                source: 抽出元のデータ（文書内容やファイルID）
                extraction_type: 抽出タイプ（"transaction_details", "amounts", "dates", "parties", "all"）

            Returns:
                抽出されたデータ
            """
            if supervisor._extract_data_fn:
                return supervisor._extract_data_fn(source, extraction_type)

            # Default implementation
            return f"[extract_data] source={source[:100]}..., type={extraction_type}"

        @tool
        def analyze_data(data: str, analysis_type: str, parameters: str = "{}") -> str:
            """
            データを分析して結果を返します。

            Args:
                data: 分析対象のデータ
                analysis_type: 分析タイプ（"compare_values", "validate_sequence", "detect_anomalies", "calculate_variance"）
                parameters: 追加パラメータ（JSON形式）

            Returns:
                分析結果
            """
            if supervisor._analyze_data_fn:
                return supervisor._analyze_data_fn(data, analysis_type, parameters)

            # Default implementation
            return f"[analyze_data] type={analysis_type}, params={parameters}"

        @tool
        def lookup_knowledge(category: str, query: str) -> str:
            """
            内部知識ベースからドメイン固有の情報を検索します。

            Args:
                category: 知識カテゴリ（"market_pricing", "vendor_profiles", "audit_rules", "compliance"）
                query: 検索クエリ

            Returns:
                関連する知識情報
            """
            if supervisor._knowledge_lookup_fn:
                result = supervisor._knowledge_lookup_fn(category, query)
                supervisor._shared_context["domain_knowledge"] = result
                return result

            # Default implementation
            return f"[lookup_knowledge] category={category}, query={query}"

        return [extract_data, analyze_data, lookup_knowledge]

    def run(self, task: str, transaction_id: str = "") -> AuditReport:
        """
        Execute a complete audit task.

        Args:
            task: The audit task description
            transaction_id: Optional transaction ID for the report

        Returns:
            AuditReport with all findings
        """
        # Clear shared context for new task
        self._shared_context.clear()

        # Stream through the agent
        final_response = ""
        for event in self._agent.stream({"messages": [{"role": "user", "content": task}]}):
            if "model" in event:
                for msg in event["model"].get("messages", []):
                    content = getattr(msg, "content", "")
                    if content:
                        final_response = content

        # Build the audit report
        return self._build_report(
            transaction_id=transaction_id or "UNKNOWN",
            task=task,
            final_response=final_response,
        )

    def stream(self, task: str):
        """
        Stream the agent's execution for real-time output.

        Args:
            task: The audit task description

        Yields:
            Events from the agent's execution
        """
        self._shared_context.clear()
        yield from self._agent.stream({"messages": [{"role": "user", "content": task}]})

    def _build_report(
        self, transaction_id: str, task: str, final_response: str
    ) -> AuditReport:
        """Build an audit report from the agent's findings."""
        hypotheses = self._shared_context.get("hypotheses", [])
        verifications = self._shared_context.get("verifications", [])

        confirmed_issues = []
        potential_issues = []
        recommendations = []

        for verification in verifications:
            if isinstance(verification, dict):
                if verification.get("verdict") == "confirmed":
                    confirmed_issues.append(verification)
                    recommendations.extend(verification.get("recommendations", []))
                elif verification.get("verdict") == "inconclusive":
                    potential_issues.append(verification)

        # Calculate confidence score
        if verifications:
            confidence_scores = [
                v.get("confidence", 0.5) for v in verifications if isinstance(v, dict)
            ]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        else:
            avg_confidence = 0.5

        return AuditReport(
            transaction_id=transaction_id,
            summary=final_response,
            confirmed_issues=confirmed_issues,
            potential_issues=potential_issues,
            recommendations=list(set(recommendations)),  # Deduplicate
            confidence_score=avg_confidence,
            agent_contributions={
                "hypothesis_agent": {
                    "hypotheses_generated": len(hypotheses),
                    "reasoning": self._shared_context.get("hypothesis_reasoning", ""),
                },
                "verifier_agent": {
                    "verifications_completed": len(verifications),
                    "reasoning": self._shared_context.get("verification_reasoning", ""),
                },
            },
        )
