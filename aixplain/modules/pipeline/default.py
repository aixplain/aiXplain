from .asset import Pipeline as PipelineAsset
from .designer import Pipeline as PipelineDesigner


class DefaultPipeline(PipelineAsset, PipelineDesigner):

    def __init__(self, *args, **kwargs):
        PipelineAsset.__init__(self, *args, **kwargs)
        PipelineDesigner.__init__(self)

    def save(self, *args, **kwargs):
        self.auto_infer()
        self.validate()
        super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        return self.serialize()
