"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Union, Dict, List 
from aixplain.modules.metadata import MetaData


def dict_to_metadata(metadatas: List[Union[Dict, MetaData]]) -> None:
    
    """Convert all the Dicts to MetaData

    Args:
        metadatas (List[Union[Dict, MetaData]], optional): metadata of metadata information of the dataset.

    """
    try:
        for i in range(len(metadatas)):
            if isinstance(metadatas[i], dict):
                metadatas[i] = MetaData(**metadatas[i])
    except TypeError:
        raise TypeError(f"Data Asset Onboarding Error: One or more elements in the metadata_schema are not well-structured")
        
    