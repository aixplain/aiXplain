import click
from aixplain.factories.model_factory import ModelFactory, test_func

@click.group('cli')
def cli():
    pass

@click.group('list')
@click.pass_context
def list(ctx):
    ctx.obj = ModelFactory()

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

list.add_command(test_func)
list.add_command(ModelFactory.list_host_machines)

def run_cli():
    cli()