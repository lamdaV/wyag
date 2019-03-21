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
from wyag.utils.objects_utils import find_repo, find_object, read_object, \
  generate_object_hash, InvalidObjectType, generate_graphviz_log, checkout_tree

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
        "hash_object": "hash-object",
        "ls_tree": "ls-tree",
        "co": "checkout"
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
@click.argument("object_name", type=click.STRING)
@click.pass_obj
def cat_file(context, object_type, object_name):
  """
  Provide content of repository objects.
  """
  repo = find_repo(os.getcwd(), context.logger)
  sha = find_object(repo, object_name, object_type=object_type)
  git_object = read_object(repo, sha)
  context.logger.echo(git_object.serialize())

@cli.command()
@click.option("--object_type", "-t", default="blob", type=click.Choice(GIT_OBJECT_TYPES, case_sensitive=False), help="Git object type to compute file as.")
@click.option("--write", "-w", default=False, is_flag=True, flag_value=True, help="Write the object into the database.")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.pass_obj
def hash_object(context, object_type, write, file):
  """
  Compute object ID and optionally creates a blob from a file.
  """
  try:
    sha = generate_object_hash(object_type, write, file, context.logger)
    context.logger.echo(sha)
  except InvalidObjectType as e:
    context.logger.error(str(e))

@cli.command()
@click.argument("commit", type=click.STRING, default="HEAD")
@click.pass_obj
def log(context, commit):
  """
  Display history of a given commit.
  """
  repo = find_repo(os.getcwd(), context.logger)
  context.logger.echo("digraph wyaglog{")
  generate_graphviz_log(repo, find_object(repo, commit), context.logger)
  context.logger.echo("}")

@cli.command()
@click.argument("git_object", type=click.STRING)
@click.pass_obj
def ls_tree(context, git_object):
  """
  "Pretty-print a tree object."
  """
  repo = find_repo(os.getcwd(), context.logger)
  object_sha = find_object(repo, git_object, object_type=b"tree")
  git_object = read_object(repo, object_sha)

  for node in git_object.data:
    padded_mode = "{}{}".format((6 - len(node.mode)) * "0", node.mode.decode("ascii"))
    object_type = read_object(repo, node.sha).object_type
    context.logger.echo("{mode} {object_type} {sha}\t{path}".format(mode=padded_mode,
                                                                    object_type=object_type,
                                                                    sha=node.sha,
                                                                    path=node.path.decode("ascii")))

@cli.command()
@click.argument("commit_sha", type=click.STRING)
@click.argument("path", type=click.Path(file_okay=False))
@click.pass_obj
def checkout(context, commit_sha, path):
  """
  Checkout a commit inside of a directory.

  commit_sha: The commit or tree to checkout.
  path: The EMPTY directory to checkout on.
  """
  repo = find_repo(os.getcwd(), context.logger)
  object_sha = find_object(repo, commit_sha)
  git_object = read_object(repo, object_sha)

  # If it is of type commit, grab the tree reference.
  if git_object.object_type == "commit":
    tree_refs = git_object.data.get(b"tree", [])
    if len(tree_refs) == 0:
      context.logger.echo("Commit object missing tree reference: {}".format(object_sha))
      return
    elif len(tree_refs) > 1:
      context.logger.echo("Commit object has more than one tree reference: sha={} refs={}".format(object_sha, tree_refs))
      return
    tree_ref, *_ = tree_refs
    git_object = read_object(repo, tree_ref.decode("ascii"))
  
  if os.path.exists(path):
    if not os.path.isdir(path):
      context.logger.echo("Not a directory: {}!".format(path))
      return
    elif len(os.listdir(path)) > 0:
      context.logger.echo("Not empty: {}!".format(path))
      return
  else:
    os.makedirs(path)

  checkout_tree(repo, git_object, os.path.realpath(path).encode())


