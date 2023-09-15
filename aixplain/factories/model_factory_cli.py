from aixplain.factories.model_factory import ModelFactory
import click

@click.command("hosts")
@click.argument('--api-key', default=None, help='Number of greetings.')
def list_host_machines(api_key):
    ret_val = ModelFactory.list_host_machines(api_key)
    click.echo(ret_val)
    return ret_val

@click.command("functions")
def list_functions(verbose):
    pass