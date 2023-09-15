import click
from aixplain.factories.model_factory import ModelFactory

@click.group('cli')
def cli():
    pass

@click.group('list')
def list():
    pass

@click.group('get')
def get():
    pass

@click.group('create')
def create():
    pass

@click.group('onboard')
def onboard():
    pass

cli.add_command(list)
cli.add_command(get)
cli.add_command(create)
cli.add_command(onboard)

def mock():
    return ModelFactory.list_host_machines(ModelFactory)
list.add_command(mock)

def run_cli():
    cli()