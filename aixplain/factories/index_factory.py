from aixplain.modules.model.index_model import IndexModel
from aixplain.factories import ModelFactory
from aixplain.enums import ResponseStatus
from typing import Text


class IndexFactory(ModelFactory):
    @classmethod
    def create(cls, name: Text, description: Text) -> IndexModel:
        """Create a new index collection"""
        model = cls.get("66eae6656eb56311f2595011")

        data = {"data": name, "description": description}
        response = model.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            model_id = response.data
            model = cls.get(model_id)
            return model

        error_message = f"Index Factory Exception: {response.error_message}"
        if error_message == "":
            error_message = "Index Factory Exception:An error occurred while creating the index collection."
        raise Exception(error_message)
