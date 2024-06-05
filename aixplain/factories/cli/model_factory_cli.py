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
    Model Factory CLI
"""

from aixplain.factories.model_factory import ModelFactory
from typing import Dict, List, Optional, Text
import click
import yaml

@click.command("hosts")
@click.option("--api-key", default=None, 
              help="TEAM_API_KEY if not already set in environment")
def list_host_machines(api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the LIST_HOST_MACHINES function in 
    ModelFactory.

    Args:
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """
    ret_val = ModelFactory.list_host_machines(api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("functions")
@click.option("--verbose", is_flag=True, 
              help="List all function details, False by default.")
@click.option("--api-key", default=None, 
              help="TEAM_API_KEY if not already set in environment.")
def list_functions(verbose: bool, api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the LIST_FUNCTIONS function in ModelFactory.

    Args:
        verbose (Boolean, optional): Set to True if a detailed response 
            is desired; is otherwise False by default.
        api_key (Text, optional): Team API key. Defaults to None.
    Returns:
        None
    """
    ret_val = ModelFactory.list_functions(verbose, api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("gpus")
@click.option("--api-key", default=None, 
              help="TEAM_API_KEY if not already set in environment.")
def list_gpus(api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the LIST_GPUS function in ModelFactory.

    Args:
        api_key (Text, optional): Team API key. Defaults to None.
    Returns:
        None
    """
    ret_val = ModelFactory.list_gpus(api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("image-repo")
@click.option("--name", help="Model name.")
@click.option("--description", help="Description of model.")
@click.option("--function", help="Function name obtained from LIST_FUNCTIONS.")
@click.option("--source-language", default="en", 
              help="Model source language in 2-character 639-1 code or 3-character 639-3 code.")
@click.option("--input-modality", help="Input type (text, video, image, etc.)")
@click.option("--output-modality", help="Output type (text, video, image, etc.)")
@click.option("--documentation-url", default="", help="Link to model documentation.")
@click.option("--api-key", default=None, 
              help="TEAM_API_KEY if not already set in environment.")
def create_asset_repo(name: Text, description: Text, function: Text,
                      source_language: Text, input_modality: Text, 
                      output_modality: Text, 
                      documentation_url: Optional[Text] = "",
                      api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the CREATE_ASSET_REPO function in ModelFactory.

    Args:
        name (Text): Model name
        hosting_machine (Text): Hosting machine ID obtained via list_host_machines
        always_on (bool): Whether the model should always be on
        version (Text): Model version
        description (Text): Model description
        function (Text): Model function name obtained via LIST_HOST_MACHINES
        is_async (bool): Whether the model is asynchronous or not (False in first release)
        source_language (Text): 2-character 639-1 code or 3-character 639-3 language code.
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """
    ret_val = ModelFactory.create_asset_repo(name, description, function, 
                                             source_language, input_modality, 
                                             output_modality, documentation_url, 
                                             api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("image-repo-login")
@click.option("--api-key", default=None, 
              help="TEAM_API_KEY if not already set in environment.")
def asset_repo_login(api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the ASSET_REPO_LOGIN function in ModelFactory.

    Args:
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """
    ret_val = ModelFactory.asset_repo_login(api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("model")
@click.option("--model-id", help="Model ID from CREATE_IMAGE_REPO.")
@click.option("--image-tag", help="The tag of the image that you would like hosted.")
@click.option("--image-hash", help="The hash of the image you would like onboarded.")
@click.option("--host-machine", default="", help="The machine on which to host the model.")
@click.option("--api-key", default=None, help="TEAM_API_KEY if not already set in environment.")
def onboard_model(model_id: Text, image_tag: Text, image_hash: Text, 
                  host_machine: Optional[Text] = "", 
                  api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the ONBOARD_MODEL function in ModelFactory.

    Args:
        model_id (Text): Model ID obtained from CREATE_ASSET_REPO.
        image_tag (Text): Image tag to be onboarded.
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """   
    ret_val = ModelFactory.onboard_model(model_id, image_tag, image_hash, 
                                         host_machine, api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("hf-model")
@click.option("--name", help="User-defined name for Hugging Face model.")
@click.option("--hf-repo-id", help="Repository ID from Hugging Face in {supplier}/{model name} form.")
@click.option("--revision", default="", help="Commit hash of repository.")
@click.option("--hf-token", default=None, help="Hugging Face token used to authenticate to this model.")
@click.option("--api-key", default=None, help="TEAM_API_KEY if not already set in environment.")
def deploy_huggingface_model(name: Text, hf_repo_id: Text, 
                             hf_token: Optional[Text] = None, 
                             revision: Optional[Text] = None,
                             api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the DEPLOY_HUGGINGFACE_MODEL function in ModelFactory.

    Args:
        name (Text): User-defined name for Hugging Face model.
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """
    ret_val = ModelFactory.deploy_huggingface_model(name, hf_repo_id, revision, hf_token, api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)

@click.command("hf-model-status")
@click.option("--model-id", help="Model ID from DEPLOY_HUGGINGFACE_MODEL.")
@click.option("--api-key", default=None, help="TEAM_API_KEY if not already set in environment.")
def get_huggingface_model_status(model_id: Text, api_key: Optional[Text] = None) -> None:
    """CLI wrapper function for the GET_HUGGINGFACE_MODEL_STATUS function in ModelFactory.

    Args:
        model_id (Text): Model ID obtained from DEPLOY_HUGGINGFACE_MODEL.
        api_key (Text, optional): Team API key. Defaults to None.

    Returns:
        None
    """
    ret_val = ModelFactory.get_huggingface_model_status(model_id, api_key)
    ret_val_yaml = yaml.dump(ret_val)
    click.echo(ret_val_yaml)
