"""
Factory module for creating Inspector v2 configuration objects.

Inspector v2 (SDK) is a pure config schema that the SDK sends to backendagentification.
"""

from typing import List, Optional, Text

from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorActionConfig,
    InspectorActionType,
    InspectorOnExhaust,
    InspectorSeverity,
)


class InspectorFactory:
    """factory class for building inspector v2 config objects"""

    @classmethod
    def create_llm(
        cls,
        *,
        name: Text,
        evaluator: Text,
        evaluator_prompt: Text,
        targets: List[Text],
        description: Optional[Text] = None,
        severity: InspectorSeverity = InspectorSeverity.LOW,
        action_type: InspectorActionType = InspectorActionType.RERUN,
        max_retries: int = 2,
        on_exhaust: InspectorOnExhaust = InspectorOnExhaust.CONTINUE,
    ) -> Inspector:
        """Create an LLM evaluator inspector config"""
        return Inspector(
            name=name,
            description=description,
            severity=severity,
            targets=targets,
            action=InspectorActionConfig(
                action_type=action_type,
                max_retries=max_retries,
                on_exhaust=on_exhaust,
                evaluator=evaluator,
                evaluator_prompt=evaluator_prompt,
            ),
        )

    @classmethod
    def create(
        cls,
        *,
        name: Text,
        targets: List[Text],
        action: InspectorActionConfig,
        description: Optional[Text] = None,
        severity: Optional[InspectorSeverity] = None,
    ) -> Inspector:
        """Create an inspector config from a fuly-specified action config"""
        return Inspector(
            name=name,
            description=description,
            severity=severity,
            targets=targets,
            action=action,
        )
