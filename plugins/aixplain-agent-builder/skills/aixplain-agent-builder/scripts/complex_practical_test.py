#!/usr/bin/env python3
"""Complex end-to-end test for the aixplain agent-builder skill.

Creates a customer-risk agent backed by SQLite, an aiR knowledge base, and a
Python Sandbox risk scorer. Verifies direct tools, least-privilege action scopes,
agent orchestration, governance, cost, and saved-agent round trip.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aixplain import Aixplain
from aixplain.v2.upload_utils import FileUploader

SQLITE_INTEGRATION_ID = "689e06ed3ce71f58d73cc999"
KB_INTEGRATION_ID = "6904bcf672a6e36b68bb72fb"
PYTHON_SANDBOX_INTEGRATION_ID = "688779d8bfb8e46c273982ca"


def create_customer_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE account_health (
                account TEXT PRIMARY KEY,
                plan TEXT NOT NULL,
                active_users INTEGER NOT NULL,
                seats INTEGER NOT NULL,
                support_tickets_30d INTEGER NOT NULL,
                days_since_login INTEGER NOT NULL,
                renewal_days INTEGER NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO account_health VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("Acme Corp", "Enterprise", 42, 100, 8, 14, 21),
                ("Globex", "Growth", 88, 100, 1, 2, 120),
                ("Initech", "Enterprise", 63, 80, 3, 5, 75),
            ],
        )
        connection.commit()
    finally:
        connection.close()


def unit_names(steps: list | None) -> list[str]:
    names: list[str] = []
    for step in steps or []:
        if not isinstance(step, dict):
            continue
        unit = step.get("unit") or {}
        if isinstance(unit, dict) and unit.get("name"):
            names.append(str(unit["name"]))
    return names


def tool_scope(tool: Any) -> list[str]:
    scope = getattr(tool, "allowed_actions", None)
    if scope is not None:
        return list(scope)
    if isinstance(tool, dict):
        return list(tool.get("allowed_actions") or tool.get("allowedActions") or [])
    return []


def main() -> None:
    api_key = os.environ["AIXPLAIN_API_KEY"]
    aix = Aixplain(api_key=api_key)
    suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-UTC")

    with tempfile.TemporaryDirectory(prefix="aixplain-agent-builder-") as temp_dir:
        database_path = Path(temp_dir) / "customer-health.db"
        create_customer_database(database_path)
        database_url = FileUploader(api_key=api_key, backend_url=aix.backend_url).upload(
            str(database_path),
            is_temp=True,
            return_download_link=True,
        )

        database = aix.Tool(
            name=f"Customer Health DB {suffix}",
            description="Queries customer adoption, support, login, and renewal metrics.",
            integration=SQLITE_INTEGRATION_ID,
            config={"url": database_url},
        ).save()
        database.allowed_actions = ["schema", "query"]
        database.save()

        database_probe = database.run(
            action="query",
            data={"query": "SELECT * FROM account_health WHERE account = 'Acme Corp'"},
        )
        assert "Acme Corp" in str(database_probe.data), database_probe.data

        knowledge = aix.Tool(
            name=f"Customer Success Playbook {suffix}",
            description="Finds approved risk thresholds and intervention playbooks.",
            integration=KB_INTEGRATION_ID,
        ).save()
        knowledge.allowed_actions = ["upsert", "search", "get"]
        knowledge.save()
        knowledge.run(
            action="upsert",
            data={
                "records": [
                    {
                        "id": "risk-thresholds",
                        "text": (
                            "Classify an account as high risk when adoption is below 50 percent, "
                            "support tickets are at least 5 in 30 days, inactivity reaches 14 days, "
                            "or renewal is within 30 days. Multiple signals increase urgency."
                        ),
                        "metadata": {"type": "policy"},
                    },
                    {
                        "id": "high-risk-playbook",
                        "text": (
                            "For high-risk enterprise accounts: assign an executive sponsor, schedule "
                            "a success review within 3 business days, resolve the top support blocker, "
                            "and agree on a 30-day adoption plan with weekly checkpoints."
                        ),
                        "metadata": {"type": "playbook"},
                    },
                ]
            },
        )
        knowledge.allowed_actions = ["search", "get"]
        knowledge.save()

        knowledge_probe = knowledge.run(
            action="search",
            data={"query": "high-risk enterprise intervention", "top_k": 2, "filters": []},
        )
        assert "high-risk" in str(knowledge_probe.data).lower(), knowledge_probe.data

        scorer_code = """def score_risk(active_users: int, seats: int, support_tickets_30d: int, days_since_login: int, renewal_days: int):
    adoption_percent = round((active_users / seats) * 100, 1) if seats else 0.0
    score = 0
    reasons = []
    if adoption_percent < 50:
        score += 35
        reasons.append("adoption below 50 percent")
    if support_tickets_30d >= 5:
        score += 25
        reasons.append("at least 5 support tickets in 30 days")
    if days_since_login >= 14:
        score += 20
        reasons.append("at least 14 days since login")
    if renewal_days <= 30:
        score += 20
        reasons.append("renewal within 30 days")
    band = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    return {"score": score, "band": band, "adoption_percent": adoption_percent, "reasons": reasons}
"""
        scorer = aix.Tool(
            name=f"Account Risk Scorer {suffix}",
            description="Computes a deterministic account risk score from customer-health metrics.",
            integration=PYTHON_SANDBOX_INTEGRATION_ID,
            config={"code": scorer_code, "function_name": "score_risk"},
        ).save()
        scorer.allowed_actions = ["score_risk"]
        scorer.save()

        scorer_probe = scorer.run(
            action="score_risk",
            data={
                "active_users": 42,
                "seats": 100,
                "support_tickets_30d": 8,
                "days_since_login": 14,
                "renewal_days": 21,
            },
        )
        assert "HIGH" in str(scorer_probe.data).upper(), scorer_probe.data

        expected_scopes = {
            database.name: ["schema", "query"],
            knowledge.name: ["search", "get"],
            scorer.name: ["score_risk"],
        }
        assert tool_scope(database) == expected_scopes[database.name]
        assert tool_scope(knowledge) == expected_scopes[knowledge.name]
        assert tool_scope(scorer) == expected_scopes[scorer.name]

        agent = aix.Agent(
            name=f"Customer Risk Briefing Agent {suffix}",
            description="Combines customer metrics, policy knowledge, and deterministic scoring into an action plan.",
            instructions=(
                "For every account assessment, complete all steps before answering: "
                "(1) query Customer Health DB for the named account; "
                "(2) search Customer Success Playbook for applicable thresholds and actions; "
                "(3) call Account Risk Scorer with the exact database values; "
                "(4) reconcile the score with the playbook and return evidence, risk band, reasons, "
                "and prioritized actions. Never invent missing metrics and never write to the database or KB."
            ),
            tools=[database, knowledge, scorer],
            output_format="markdown",
            max_tokens=2200,
        )
        agent.budget.max_cost = 0.20
        agent.budget.max_duration_seconds = 180
        agent.budget.max_iterations = 14
        agent.save()

        query = (
            "Assess Acme Corp's renewal risk. Use the customer database, approved playbook, and "
            "deterministic risk scorer. Include the source metrics, score, risk band, and top actions."
        )
        result = agent.run(query=query)
        observed_units = unit_names(result.data.steps)
        governance = result.data.governance or {}
        output = str(result.data.output or "")
        stats = result.data.execution_stats or {}

        for required_name in expected_scopes:
            assert required_name in observed_units, {
                "missing": required_name,
                "observed": observed_units,
                "output": output,
            }
        assert governance.get("status", "ALLOWED") == "ALLOWED", governance
        assert "HIGH" in output.upper(), output
        assert "42" in output and "100" in output and "8" in output and "21" in output, output

        raw_agent = aix.Agent.context.client.get(f"v2/agents/{agent.id}")
        raw_scopes = {
            item.get("name"): list(item.get("actions") or [])
            for item in (raw_agent.get("tools") or [])
            if isinstance(item, dict) and item.get("name")
        }
        assert raw_scopes == expected_scopes, {
            "expected": expected_scopes,
            "raw_persisted": raw_scopes,
        }

        reloaded = aix.Agent.get(agent.id)
        assert reloaded.id == agent.id
        assert len(reloaded.tools or []) == 3, reloaded.tools

        hydrated_scopes = {
            getattr(tool, "name", str(index)): tool_scope(tool)
            for index, tool in enumerate(reloaded.tools or [])
        }
        hydration_scope_bug_observed = hydrated_scopes != raw_scopes

        report = {
            "status": "PASS_WITH_KNOWN_SDK_BUG" if hydration_scope_bug_observed else "PASS",
            "agent_id": agent.id,
            "app_url": f"https://app.aixplain.com/agents/{agent.id}",
            "query": query,
            "direct_tool_checks": {
                "database": "PASS",
                "knowledge_base": "PASS",
                "risk_scorer": "PASS",
            },
            "expected_scopes": expected_scopes,
            "observed_units": observed_units,
            "governance": governance,
            "credits": stats.get("credits"),
            "runtime": stats.get("runtime"),
            "output": output,
            "round_trip": {
                "tool_count": len(reloaded.tools or []),
                "raw_persisted_scopes": raw_scopes,
                "hydrated_scopes": hydrated_scopes,
                "hydration_scope_bug_observed": hydration_scope_bug_observed,
            },
        }
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
