from aixplain.factories.model_factory import ModelFactory
import click

@click.command("hosts")
def list_host_machines():
    ret_val = ModelFactory.list_host_machines()
    click.echo(ret_val)
    return ret_val