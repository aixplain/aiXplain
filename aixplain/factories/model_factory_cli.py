from aixplain.factories.model_factory import ModelFactory
import click

@click.command("hosts")
@click.option("--api-key", default=None)
def list_host_machines(api_key):
    ret_val = ModelFactory.list_host_machines(api_key)
    click.echo(ret_val)
    return ret_val

@click.command("functions")
@click.option('--verbose', default=False)
def list_functions(verbose, api_key):
    ret_val = ModelFactory.list_functions(verbose, api_key)
    click.echo(ret_val)
    return ret_val