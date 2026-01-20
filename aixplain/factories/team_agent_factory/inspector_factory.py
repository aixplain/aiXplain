"""
Factory module for creating Inspector v2 configuration objects.

Inspector v2 (SDK) is a pure config schema that the SDK sends to backendagentification.
"""

from typing import List, Optional, Text

from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorActionConfig,
    Inspectoraction_type,
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
        actionType: Inspectoraction_type = Inspectoraction_type.RERUN,
        maxRetries: int = 2,
        onExhaust: InspectorOnExhaust = InspectorOnExhaust.CONTINUE,
    ) -> Inspector:
        """Create an LLM evaluator inspector config"""
        return Inspector(
            name=name,
            description=description,
            severity=severity,
            targets=targets,
            action=InspectorActionConfig(
                actionType=actionType,
                maxRetries=maxRetries,
                onExhaust=onExhaust,
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
