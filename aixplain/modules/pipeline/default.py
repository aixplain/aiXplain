from .asset import Pipeline as PipelineAsset
from .designer import DesignerPipeline


class DefaultPipeline(PipelineAsset, DesignerPipeline):

    def __init__(self, *args, **kwargs):
        PipelineAsset.__init__(self, *args, **kwargs)
        DesignerPipeline.__init__(self)

    def save(self, *args, **kwargs):
        self.auto_infer()
        self.validate()
        super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        return self.serialize()
