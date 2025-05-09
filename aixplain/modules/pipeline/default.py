from .asset import Pipeline as PipelineAsset
from .designer import DesignerPipeline
from enum import Enum


class DefaultPipeline(PipelineAsset, DesignerPipeline):
    def __init__(self, *args, **kwargs):
        PipelineAsset.__init__(self, *args, **kwargs)
        DesignerPipeline.__init__(self)

    def save(self, *args, **kwargs):
        self.auto_infer()
        self.validate()
        super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        data = self.__dict__.copy()

        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value

            elif isinstance(value, list):
                data[key] = [
                    v.to_dict() if hasattr(v, "to_dict") else str(v) for v in value
                ]

            elif hasattr(value, "to_dict"):
                data[key] = value.to_dict()

        return data
