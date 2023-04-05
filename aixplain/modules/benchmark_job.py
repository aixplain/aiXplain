__author__='shreyassharma'

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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: December 2nd 2022
Description:
    Benchmark Job Class
"""

class BenchmarkJob:
    """"Benchmark Job Represents a single run of an already created Benchmark.

    Attributes:
        id (str): ID of the Benchmark Job.
        status (str): Status of the Benchmark Job.
        parentBenchmarkId (str): ID of the associated parent Benchmark.
        additional_info (dict): Any additional information to be saved with the Benchmark Job.
 
    """
    def __init__(self, id:str, status:str, parentBenchmarkId: str, **additional_info) -> None:
        """Create a Benchmark Job with the necessary information. Each Job is a run of a parent Benchmark

        Args:
            id (str): ID of the Benchmark Job
            status (str): Status of the Benchmark Job
            parentBenchmarkId (str): ID of the associated parent Benchmark
            **additional_info: Any additional Benchmark Job info to be saved
        """
        self.id = id
        self.status = status
        self.parentBenchmarkId = parentBenchmarkId
        self.additional_info = additional_info
    

    def get_asset_info(self) -> dict:
        """Get the Benchmark Job info as a Dictionary

        Returns:
            dict: Benchmark Job Information
        """
        return self.__dict__

    
    