import click
import collections
import configparser
import hashlib
import os
import re
import zlib

from wyag.objects.repository import Repository, RepositoryInitializationError
from wyag.utils.logger import Logger

class Context(object):
  def __init__(self, verbose):
    self.verbose = verbose
    self.logger = Logger(self.verbose)


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False, flag_value=True, help="Enable verbose logging")
@click.pass_context
def cli(context, verbose):
  context.obj = Context(verbose)


@cli.command()
@click.argument("path", required=False, default=os.getcwd())
@click.pass_obj
def init(context, path):
  repo = Repository(path, force=True, logger=context.logger)
  error_code = 0
  try:
    repo.initialize()
  except RepositoryInitializationError as e:
    context.logger.error(str(e))
    error_code = 1
  finally:
    exit(error_code)

@cli.command()
def echo():
  click.echo("hello world")
