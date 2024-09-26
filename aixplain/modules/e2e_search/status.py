from aixplain.enums.asset_status import AssetStatus
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional, Text

@dataclass_json
@dataclass
class E2eSearchStatus(object):
    status: "AssetStatus"
    model_status: "AssetStatus"
    validation_metric: Optional[Text] = None
    best_validation_score: Optional[float] = None
