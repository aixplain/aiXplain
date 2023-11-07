from typing import List, Text
from aixplain.modules.dataset import Dataset
import re


def _get_data_list(dataset: Dataset):
    flatten_target_values = [item for sublist in list(dataset.target_data.values()) for item in sublist]
    data_list = list(dataset.source_data.values()) + flatten_target_values
    return data_list


def validate_prompt(prompt: Text, dataset_list: List[Dataset]) -> Text:
    result_prompt = prompt
    referenced_data = set(re.findall("<<(.+?)>>", prompt))
    for dataset in dataset_list:
        data_list = _get_data_list(dataset)
        for data in data_list:
            if data.id in referenced_data:
                result_prompt = result_prompt.replace(f"<<{data.id}>>", f"<<{data.name}>>")
                referenced_data.remove(data.id)
                referenced_data.add(data.name)

    # check if dataset list has same data name and it is referenced
    name_set = set()
    for dataset in dataset_list:
        data_list = _get_data_list(dataset)
        for data in data_list:
            assert not (
                data.name in name_set and data.name in referenced_data
            ), "Datasets must not have more than one referenced data with same name"
            name_set.add(data.name)

    # check if all referenced data have a respective data in dataset list
    for dataset in dataset_list:
        data_list = _get_data_list(dataset)
        for data in data_list:
            if data.name in referenced_data:
                result_prompt = result_prompt.replace(f"<<{data.name}>>", f"{{{data.name}}}")
                referenced_data.remove(data.name)
    assert len(referenced_data) == 0, "Referenced data are not present in dataset list"
    return result_prompt
