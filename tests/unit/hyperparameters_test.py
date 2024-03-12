__author__ = "lucaspavanelli"

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

from dotenv import load_dotenv

load_dotenv()

from aixplain.modules.finetune import Hyperparameters
from aixplain.modules.finetune.hyperparameters import (
    EPOCHS_MAX_VALUE,
    BATCH_SIZE_VALUES,
    MAX_SEQ_LENGTH_MAX_VALUE,
)


import pytest


def test_create():
    hyp = Hyperparameters()
    assert hyp is not None


@pytest.mark.parametrize(
    "params",
    [
        {"epochs": "string"},
        {"train_batch_size": "string"},
        {"eval_batch_size": "string"},
        {"learning_rate": "string"},
        {"max_seq_length": "string"},
        {"warmup_ratio": "string"},
        {"warmup_steps": "string"},
        {"lr_scheduler_type": "string"},
    ],
)
def test_create_invalid_type(params):
    with pytest.raises(Exception) as exc_info:
        Hyperparameters(**params)
    assert exc_info.type is TypeError


@pytest.mark.parametrize(
    "params",
    [
        {"epochs": EPOCHS_MAX_VALUE + 1},
        {"train_batch_size": max(BATCH_SIZE_VALUES) + 1},
        {"eval_batch_size": max(BATCH_SIZE_VALUES) + 1},
        {"max_seq_length": MAX_SEQ_LENGTH_MAX_VALUE + 1},
    ],
)
def test_create_invalid_values(params):
    with pytest.raises(Exception) as exc_info:
        Hyperparameters(**params)
    assert exc_info.type is ValueError
