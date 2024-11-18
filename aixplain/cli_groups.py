__author__ = "aiXplain"

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

Author: Michael Lam
Date: September 18th 2023
Description:
    CLI Runner
"""
import click
from aixplain.factories.cli.model_factory_cli import (
    list_host_machines,
    list_functions,
    create_asset_repo,
    asset_repo_login,
    onboard_model,
    deploy_huggingface_model,
    get_huggingface_model_status,
    list_gpus,
)


@click.group("cli")
def cli():
    pass


@click.group("list")
def list():
    pass


@click.group("get")
def get():
    pass


@click.group("create")
def create():
    pass


@click.group("onboard")
def onboard():
    pass


cli.add_command(list)
cli.add_command(get)
cli.add_command(create)
cli.add_command(onboard)

create.add_command(create_asset_repo)
list.add_command(list_host_machines)
list.add_command(list_functions)
list.add_command(list_gpus)
get.add_command(asset_repo_login)
get.add_command(get_huggingface_model_status)
onboard.add_command(onboard_model)
onboard.add_command(deploy_huggingface_model)


def run_cli():
    cli()
