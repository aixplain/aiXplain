
from aixplain.modules.model.index_model import IndexModel
from aixplain.factories import ModelFactory

class IndexModelFactory:
    @staticmethod
    def get(model_id: str) -> IndexModel:
        model = ModelFactory.get(model_id)
        return IndexModel(
            id=model.id,
            name=model.name,
            description=model.description,
            api_key=model.api_key,
            supplier=model.supplier,
            version=model.version,
            function=model.function,
            is_subscribed=model.is_subscribed,
            cost=model.cost,
            created_at=model.created_at,
            input_params=model.input_params,
            output_params=model.output_params,
            **model.additional_info,
        )
