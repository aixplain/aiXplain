__author__ = "thiagocastroferreira"

"""
Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira
Date: September 27th 2023
Description:
    Pipeline Output Factory Class
"""

from aixplain.enums.data_type import DataType
from aixplain.enums.language import Language
from aixplain.outputs.pipelines import PipelineOutput
from aixplain.outputs.pipelines.input_info import InputInfo
from aixplain.outputs.pipelines.output_node import OutputNode
from aixplain.outputs.pipelines.output_segment import OutputSegment
from typing import Dict, Text


def get_data_type(data_type_str: Text) -> DataType:
    """Data Type Getter

    Args:
        data_type_str (Text): data type value

    Raises:
        Exception: data type value does not exist

    Returns:
        DataType: data type enumerator
    """
    try:
        data_type = DataType(data_type_str)
    except Exception:
        raise Exception(f"Data type '{data_type_str}' does not exist.")
    return data_type


def get_language(language_str: Text) -> Language:
    """Language Getter

    Args:
        language_str (Text): language value string

    Raises:
        Exception: language value does not exist

    Returns:
        Language: language enumerator
    """
    try:
        language = Language({"language": language_str, "dialect": ""})
    except Exception:
        raise Exception(f"Language '{language_str}' does not exist.")
    return language


def create_input_info(input_info_dict: Dict) -> InputInfo:
    """InputInfo setter

    Args:
        input_info_dict (Dict): input info dictionary

    Returns:
        InputInfo: InputInfo object
    """
    start = input_info_dict["start"]
    end = input_info_dict["end"]
    length = input_info_dict["length"]
    is_url = input_info_dict["is_url"]
    data_type = get_data_type(input_info_dict["type"])
    input_segment = input_info_dict["segment"]
    language = None
    if "language" in input_info_dict:
        language = get_language(input_info_dict["language"])

    return InputInfo(
        start=start, end=end, length=length, is_url=is_url, language=language, data_type=data_type, input_segment=input_segment
    )


def create_output_segment(output_segment_dict: Dict) -> OutputSegment:
    """OutputSegment Setter

    Args:
        output_segment_dict (Dict): output segment dictionary

    Returns:
        OutputSegment: OutputSegment instance
    """
    index = output_segment_dict["index"]
    status = "SUCCESS" if output_segment_dict["success"] is True else "FAILED"
    response = output_segment_dict["response"]
    is_url = output_segment_dict["is_url"]
    data_type = get_data_type(output_segment_dict["output_type"])
    language = None
    if "language" in output_segment_dict:
        language = get_language(output_segment_dict["language"])
    details = output_segment_dict["details"]
    supplier_response = None
    if "rawData" in details:
        supplier_response = details["rawData"]
        del details["rawData"]
    input_info = [create_input_info(info) for info in output_segment_dict["input_segment_info"]]

    return OutputSegment(
        index=index,
        status=status,
        response=response,
        is_url=is_url,
        data_type=data_type,
        details=details,
        supplier_response=supplier_response,
        language=language,
        input_info=input_info,
    )


def create_output_node(output_node_dict: Dict) -> OutputNode:
    """OutputNode Setter

    Args:
        output_node_dict (Dict): output node dictionary

    Returns:
        OutputNode: OutputNode instance
    """
    node_id = output_node_dict["node_id"]
    label = output_node_dict["label"]
    path = output_node_dict["path"]
    outputs = [create_output_segment(output_segment_dict) for output_segment_dict in output_node_dict["segments"]]
    is_segmented = output_node_dict["is_segmented"]

    return OutputNode(node_id=node_id, label=label, path=path, outputs=outputs, is_segmented=is_segmented)


class PipelineOutputFactory:
    """A static class for creating and exploring Pipeline Output Objects."""

    @classmethod
    def create_success_output(cls, response: Dict) -> PipelineOutput:
        elapsed_time = response["elapsed_time"]
        used_credits = response["used_credits"]
        output_nodes = [create_output_node(output_node_dict) for output_node_dict in response["data"]]

        return PipelineOutput(status="SUCCESS", output_nodes=output_nodes, elapsed_time=elapsed_time, used_credits=used_credits)

    @classmethod
    def create_in_progress_output(cls, progress: Text, elapsed_time: float = 0, used_credits: float = 0) -> PipelineOutput:
        return PipelineOutput(
            status="IN_PROGRESS", output_nodes=[], elapsed_time=elapsed_time, used_credits=used_credits, progress=progress
        )

    @classmethod
    def create_fail_output(cls, error_message: Text, elapsed_time: float = 0, used_credits: float = 0) -> PipelineOutput:
        return PipelineOutput(
            status="FAILED",
            output_nodes=[],
            elapsed_time=elapsed_time,
            used_credits=used_credits,
            progress="0%",
            error_message=error_message,
        )
