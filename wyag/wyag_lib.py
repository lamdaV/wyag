import click

@click.group()
def cli():
  pass

@cli.command()
def echo():
  click.echo("hello world")

