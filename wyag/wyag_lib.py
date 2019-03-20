import click
import collections
import configparser
import hashlib
import os
import re
import zlib

from wyag.objects.repository import Repository, RepositoryInitializationError
from wyag.objects.git_object import GIT_OBJECT_TYPES
from wyag.utils.logger import Logger
from wyag.utils.objects_utils import repo_find, find_object, read_object, \
  generate_object_hash, InvalidObjectType

class Context(object):
  def __init__(self, verbose):
    self.verbose = verbose
    self.logger = Logger(self.verbose)

class AliasedGroup(click.Group):
    """
    This subclass of a group supports looking up aliases in a config
    file and with a bit of magic.
    """

    def get_command(self, context, command_name):
      # Step one: bulitin commands as normal
      rv = click.Group.get_command(self, context, command_name)
      if rv is not None:
          return rv

      # Step two: lookup an explicit command alias
      alias = {
        "cat_file": "cat-file",
        "hash_object": "hash-object"
      }
      aliased_command = alias.get(command_name, None)
      if aliased_command is not None:
        return click.Group.get_command(self, context, aliased_command)

      return None


@click.group(cls=AliasedGroup)
@click.option("--verbose", "-v", is_flag=True, default=False, flag_value=True, help="Enable verbose logging")
@click.pass_context
def cli(context, verbose):
  context.obj = Context(verbose)


@cli.command()
@click.argument("path", required=False, default=os.getcwd(), type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True))
@click.pass_obj
def init(context, path):
  """
  Initialize a new, empty repository.
  """
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
@click.argument("object_type", type=click.Choice(GIT_OBJECT_TYPES, case_sensitive=False))
@click.argument("object_name")
@click.pass_obj
def cat_file(context, object_type, object_name):
  """
  Provide content of repository objects.
  """
  repo = repo_find(os.getcwd(), context.logger)
  sha = find_object(repo, object_name, object_type=object_type)
  git_object = read_object(repo, sha)
  context.logger.echo(git_object.serialize())

@cli.command()
@click.option("--object_type", "-t", default="blob", type=click.Choice(GIT_OBJECT_TYPES, case_sensitive=False), help="Git object type to compute file as.")
@click.option("--write", "-w", default=False, is_flag=True, flag_value=True, help="Write the object into the database.")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
def hash_object(context, object_type, write, file):
  try:
    sha = generate_object_hash(object_type, write, file, context.logger)
    context.logger.echo(sha)
  except InvalidObjectType as e:
    context.logger.error(str(e))
  


@cli.command()
def echo():
  click.echo("hello world")
