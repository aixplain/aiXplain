from .asset import Pipeline as PipelineAsset
from .designer import DesignerPipeline
from enum import Enum


class DefaultPipeline(PipelineAsset, DesignerPipeline):
    """
    DefaultPipeline is a subclass of PipelineAsset and DesignerPipeline.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the DefaultPipeline.
        """
        PipelineAsset.__init__(self, *args, **kwargs)
        DesignerPipeline.__init__(self)

    def save(self, *args, **kwargs):
        """
        Save the DefaultPipeline.
        """
        self.auto_infer()
        self.validate()
        super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        """
        Convert the DefaultPipeline to a dictionary.
        """
        return self.serialize()
    