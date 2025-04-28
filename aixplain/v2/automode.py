import logging
from enum import Enum
from typing import List, Union, Optional, Any, TypeVar, Generic, Callable, Dict
from collections import Counter

from aixplain.factories.model_factory import ModelFactory
from aixplain.factories.pipeline_factory import PipelineFactory
from .resource import BaseResource

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseResource)


class Mapper(Generic[T]):
    """Base class for mappers that sort assets."""

    def map(self, assets: List[T]) -> List[T]:
        """Sort assets based on specific criteria.

        Args:
            assets: List of assets to sort.

        Returns:
            Sorted list of assets.
        """
        raise NotImplementedError("Subclasses must implement this method")


class Reducer(Generic[T]):
    """Base class for reducers that filter assets."""

    def reduce(self, assets: List[T]) -> List[T]:
        """Filter assets based on specific criteria.

        Args:
            assets: List of assets to filter.

        Returns:
            Filtered list of assets.
        """
        raise NotImplementedError("Subclasses must implement this method")


class AttributeMapper(Mapper[T]):
    """Mapper that sorts assets based on an attribute."""

    def __init__(self, attribute: str, reverse: bool = True):
        """Initialize an AttributeMapper.

        Args:
            attribute: The attribute name to sort by.
            reverse: Whether to sort in descending order (default: True).
        """
        self.attribute = attribute
        self.reverse = reverse

    def map(self, assets: List[T]) -> List[T]:
        """Sort assets based on the specified attribute.

        Args:
            assets: List of assets to sort.

        Returns:
            List of sorted assets.
        """
        try:
            return sorted(
                assets,
                key=lambda x: getattr(x, self.attribute, 0),
                reverse=self.reverse,
            )
        except (AttributeError, TypeError) as e:
            logger.warning(
                f"Failed to sort by {self.attribute}: {str(e)}. "
                "Returning unsorted assets."
            )
            return assets


class PredicateReducer(Reducer[T]):
    """Reducer that filters assets based on a predicate function."""

    def __init__(self, predicate: Callable[[T], bool], exclude: bool = False):
        """Initialize a PredicateReducer.

        Args:
            predicate: A function that returns True for assets to keep.
            exclude: If True, filter out assets where predicate returns True.
        """
        self.predicate = predicate
        self.exclude = exclude

    def reduce(self, assets: List[T]) -> List[T]:
        """Filter assets based on the predicate.

        Args:
            assets: List of assets to filter.

        Returns:
            Filtered list of assets.
        """
        try:
            return [a for a in assets if self.predicate(a) != self.exclude]
        except Exception as e:
            logger.warning(
                f"Predicate evaluation failed: {str(e)}. "
                "Returning unfiltered assets."
            )
            return assets


class AutomodeSortBy(Enum):
    """Enum of available sorting criteria for Automode."""

    POPULARITY_ASC = AttributeMapper("popularity", reverse=False)
    POPULARITY_DESC = AttributeMapper("popularity", reverse=True)
    SUCCESS_RATE_ASC = AttributeMapper("success_rate", reverse=False)
    SUCCESS_RATE_DESC = AttributeMapper("success_rate", reverse=True)
    AVERAGE_LATENCY_ASC = AttributeMapper("average_latency", reverse=False)
    AVERAGE_LATENCY_DESC = AttributeMapper("average_latency", reverse=True)
    COST_ASC = AttributeMapper("cost", reverse=False)
    COST_DESC = AttributeMapper("cost", reverse=True)


class MapReduceIterator(Generic[T]):
    """Iterator class for the MapReduce process."""

    def __init__(
        self,
        assets: List[T],
        mapper: Optional[Mapper[T]] = None,
        reducers: Optional[List[Reducer[T]]] = None,
    ):
        """Initialize a MapReduceIterator.

        Args:
            assets: List of assets to process.
            mapper: Optional mapper for sorting assets.
            reducers: Optional list of reducers for filtering assets.
        """
        self.original_assets = assets
        self.mapper = mapper
        self.reducers = reducers or []
        self.processed_assets = self._process_assets()
        self.index = 0

    def _process_assets(self) -> List[T]:
        """Process assets through the MapReduce pipeline.

        Returns:
            Processed list of assets.
        """
        result = self.original_assets.copy()

        if not result:
            return []

        # Apply mapper if provided
        if self.mapper:
            try:
                result = self.mapper.map(result)
            except Exception as e:
                logger.warning(f"Mapping failed: {str(e)}. Using original order.")

        # Apply reducers in sequence
        for reducer in self.reducers:
            try:
                filtered = reducer.reduce(result)
                # Don't use an empty result from a reducer - keep the previous result
                if filtered:
                    result = filtered
                else:
                    logger.warning(
                        "Reducer returned empty result. "
                        "Keeping previous filtered assets."
                    )
            except Exception as e:
                logger.warning(f"Reducer failed: {str(e)}. Skipping.")

        return result

    def __iter__(self) -> "MapReduceIterator[T]":
        """Return self as iterator."""
        return self

    def __next__(self) -> T:
        """Get the next asset in the processed list.

        Returns:
            Next asset.

        Raises:
            StopIteration: When there are no more assets.
        """
        if self.index >= len(self.processed_assets):
            raise StopIteration

        asset = self.processed_assets[self.index]
        self.index += 1
        return asset

    def reset(self) -> None:
        """Reset the iterator to the beginning."""
        self.index = 0


class Automode(BaseResource):
    """Automode for selecting and running the best asset with fallback capability.

    Automode selects assets based on sort criteria and filters, then attempts
    to run them in order until one succeeds.

    Example:
        Simple usage with model IDs and cost optimization:

        ```python
        # Create Automode with model IDs, sorting by lowest cost first
        automode = Automode(
            asset_ids=["model-123", "model-456", "model-789"],
            sort_by=AutomodeSortBy.COST_ASC
        )

        # Run with input data
        result = automode.run({"text": "Translate this to French"})
        ```

        Advanced usage with filtering and model objects:

        ```python
        from aixplain.v2 import Model

        # Get model objects
        models = [
            Model.get("model-123"),
            Model.get("model-456"),
            Model.get("model-789")
        ]

        # Define a filter for models with success rate above 90%
        def high_success_rate(model):
            return getattr(model, "success_rate", 0) > 0.9

        # Create Automode with models, sorting by latency,
        # and filtering for high success rate
        automode = Automode(
            asset_ids=models,
            sort_by=AutomodeSortBy.AVERAGE_LATENCY_ASC,
            reducers=[create_filter(high_success_rate)]
        )

        # Run with input data
        result = automode.run({"text": "Translate this to German"})
        ```

        Mixed model and pipeline usage with multiple filters:

        ```python
        # Load models and pipelines
        assets = [Model.get("model-123"), Pipeline.get("pipeline-456")]

        # Define filters
        def not_deprecated(asset):
            return not getattr(asset, "deprecated", False)

        def supports_batch(asset):
            return getattr(asset, "supports_batch", False)

        # Create Automode with popularity sorting and multiple filters
        automode = Automode(
            asset_ids=assets,
            sort_by=AutomodeSortBy.POPULARITY_DESC,
            reducers=[
                create_filter(not_deprecated),
                create_filter(supports_batch)
            ]
        )

        # Run with batch data
        results = automode.run({"texts": ["Hello", "World", "Example"]})
        ```
    """

    def __init__(
        self,
        asset_ids: List[Union[str, BaseResource]],
        sort_by: Optional[AutomodeSortBy] = None,
        reducers: Optional[List[Reducer]] = None,
        obj: Optional[dict] = None,
    ):
        """Initialize Automode.

        Args:
            asset_ids: List of assets or asset IDs.
            sort_by: Optional sorting criteria.
            reducers: Optional list of reducers to filter assets.
            obj: Optional dictionary with additional attributes.
        """
        super().__init__(obj or {})
        self.asset_ids = asset_ids
        self.sort_by = sort_by
        self.reducers = reducers or []

    def validate(self) -> None:
        """Validate the Automode configuration.

        Ensures:
        - At least one asset is provided
        - All assets exist
        - All assets have compatible input/output types

        Raises:
            ValueError: If validation fails.
        """
        if not self.asset_ids:
            raise ValueError("At least one asset must be provided")

        # Resolve string IDs to actual assets
        for i, asset_id in enumerate(self.asset_ids):
            if isinstance(asset_id, str):
                try:
                    asset = ModelFactory.get(asset_id)
                    self.asset_ids[i] = asset
                    logger.debug(f"Resolved model asset: {asset_id}")
                except Exception:
                    try:
                        asset = PipelineFactory.get(asset_id)
                        self.asset_ids[i] = asset
                        logger.debug(f"Resolved pipeline asset: {asset_id}")
                    except Exception as e:
                        logger.error(f"Failed to resolve asset {asset_id}: {str(e)}")
                        raise ValueError(f"Asset {asset_id} not found")

        self._validate_input_output_compatibility()

    def _validate_input_output_compatibility(self) -> None:
        """Validate that all assets have compatible input/output types.

        Uses Counter objects to ensure exact matching of parameter types
        including duplicates.

        Raises:
            ValueError: If assets have incompatible types.
        """
        if not self.asset_ids:
            return

        reference_asset = self.asset_ids[0]

        # Extract input/output types from reference asset
        try:
            ref_input_types = [param.dataType for param in reference_asset.input_params]
            ref_output_types = [
                param.dataType for param in reference_asset.output_params
            ]

            # Use Counter to account for duplicates
            ref_input_counter = Counter(ref_input_types)
            ref_output_counter = Counter(ref_output_types)

        except (AttributeError, TypeError) as e:
            logger.warning(
                f"Failed to extract types from reference asset: {str(e)}. "
                "Skipping compatibility check."
            )
            return

        # Check each asset against the reference
        for asset in self.asset_ids[1:]:
            try:
                # Get types as list to preserve order and duplicates
                input_types = [param.dataType for param in asset.input_params]
                output_types = [param.dataType for param in asset.output_params]

                # Use Counter to account for duplicates
                input_counter = Counter(input_types)
                output_counter = Counter(output_types)

                # Compare the counters
                if input_counter != ref_input_counter:
                    logger.error(
                        f"Input type mismatch: {input_types} vs " f"{ref_input_types}"
                    )
                    raise ValueError(f"Asset {asset.id} has incompatible input types")

                if output_counter != ref_output_counter:
                    logger.error(
                        f"Output type mismatch: {output_types} vs "
                        f"{ref_output_types}"
                    )
                    raise ValueError(f"Asset {asset.id} has incompatible output types")
            except (AttributeError, TypeError) as e:
                logger.warning(f"Failed to check compatibility for asset: {str(e)}")
                raise ValueError(f"Asset {asset.id} has invalid type configuration")

    def _is_result_successful(self, result: Any) -> bool:
        """Check if a result is successful.

        This method handles various result object types in the aiXplain ecosystem.

        Args:
            result: The result object from an asset run.

        Returns:
            True if the result indicates success, False otherwise.
        """
        # Handle basic None case
        if result is None:
            return False

        # Handle dictionary-like results (including result objects with __getitem__)
        try:
            # Check for status field
            if hasattr(result, "get") and callable(result.get):
                status = result.get("status")
                if status and status.lower() == "success":
                    return True

            # Check for status attribute
            if hasattr(result, "status"):
                status = result.status
                if status and isinstance(status, str) and status.lower() == "success":
                    return True

            # Check for success attribute/method
            if hasattr(result, "success"):
                success = result.success
                if callable(success):
                    return bool(success())
                return bool(success)

            # Check for is_success attribute/method
            if hasattr(result, "is_success"):
                is_success = result.is_success
                if callable(is_success):
                    return bool(is_success())
                return bool(is_success)

            # Check for error attribute
            if hasattr(result, "error"):
                error = result.error
                if error is None:
                    return True
                if callable(error):
                    return not bool(error())
                return not bool(error)

        except Exception as e:
            logger.warning(
                f"Error checking result success: {str(e)}. " "Treating as failure."
            )
            return False

        # If we get here and the result is truthy, assume success
        return bool(result)

    def run(self, data: Dict[str, Any]) -> Any:
        """Run assets in priority order until one succeeds.

        Args:
            data: Input data for the assets.

        Returns:
            Result from the first successful asset.

        Raises:
            RuntimeError: If all assets fail to execute.
        """
        self.validate()

        # Create iterator over processed assets
        iterator = MapReduceIterator(
            self.asset_ids,
            mapper=self.sort_by.value if self.sort_by else None,
            reducers=self.reducers,
        )

        errors = []

        # Try each asset in turn
        for asset in iterator:
            try:
                logger.info(f"Trying asset: {asset.id}")
                result = asset.run(data)

                # Check for successful execution
                if self._is_result_successful(result):
                    logger.info(f"Asset {asset.id} succeeded")
                    return result
                else:
                    # Create an informative error message
                    error_info = ""
                    if hasattr(result, "error") and result.error:
                        error_info = f": {result.error}"
                    elif hasattr(result, "status"):
                        error_info = f": {result.status}"

                    error_msg = f"Asset {asset.id} execution failed{error_info}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            except Exception as e:
                error_msg = f"Asset {asset.id} execution failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

        # If we get here, all assets failed
        error_details = "\n".join(errors)
        error_message = f"All assets failed to execute. Errors:\n{error_details}"
        logger.error(error_message)
        raise RuntimeError(error_message)


# Convenience function to create a predicate reducer
def create_filter(
    predicate: Callable[[BaseResource], bool], exclude: bool = False
) -> PredicateReducer:
    """Create a filter reducer from a predicate function.

    Args:
        predicate: Function that returns True for assets to keep.
        exclude: If True, filter out assets where predicate returns True.

    Returns:
        PredicateReducer instance.
    """
    return PredicateReducer(predicate, exclude)
