import os
import zlib
import hashlib

from wyag.objects.repository import Repository
from wyag.objects.git_object import GIT_OBJECT_TYPE_TO_CLASS, GIT_OBJECT_TYPES
  
class RepositoryNotFound(Exception):
  pass
  
def find_repo(path, logger, required=True):
  logger.info("find_repo called with: {}".format({"path": path, "logger": logger, "required": required}))
  path = path if path[-1] != os.sep else path[:-1]
  real_path = os.path.realpath(path)

  if os.path.isdir(os.path.join(real_path, ".git")):
    return Repository(real_path, logger)
  
  parent = os.path.dirname(real_path)
  if parent == path:
    if required:
      raise RepositoryNotFound("No git directory")
    else:
      return None
  return find_repo(parent, logger, required=required)

class MalformedObject(Exception):
  pass

def read_object(repo, sha):
  object_path = repo.repo_file("objects", sha[:2], sha[2:])

  with open(object_path, "rb") as object_file:
    raw_object_file = zlib.decompress(object_file.read())
    space_index = raw_object_file.find(b" ")
    if space_index == -1:
      raise MalformedObject("Missing space separator in {}".format(object_path))
    object_type = raw_object_file[:space_index]

    null_index = raw_object_file.find(b"\x00")
    expect_size = int(raw_object_file[space_index + 1:null_index].decode("ascii"))
    actual_size = len(raw_object_file) - null_index - 1
    if expect_size != actual_size:
      raise MalformedObject("Invalid size: {} != {}".format(expect_size, actual_size))
    data = raw_object_file[null_index + 1:]

    git_object = GIT_OBJECT_TYPE_TO_CLASS.get(object_type.decode(), None)
    if git_object is None:
      raise MalformedObject("Invalid object_type: {}".format(object_type))

    git_object = git_object(repo, data)
    git_object.initialize()
    return git_object

def write_object(git_object, write=True):
  data = git_object.serialize()
  result = "{object_type}{space}{size}{null}{data}".format(object_type=git_object.object_type,
                                                           space=" ",
                                                           size=str(len(data)),
                                                           null="\x00",
                                                           data=data).encode()
  sha = hashlib.sha1(result).hexdigest()

  # NOTE: git_object.repo may be None if poorly initialized.
  if write and git_object.repo is not None:
    object_path = git_object.repo.repo_file("objects", sha[:2], sha[2:], mkdir=write)
    with open(object_path, "wb") as object_file:
      object_file.write(zlib.compress(result))
  
  return sha

class InvalidObjectType(Exception):
  pass

def generate_object_hash(object_type, write, file, logger):
  repo = Repository(os.getcwd(), logger) if write else None
  with open(file, "r") as file_descriptor:
    data = file_descriptor.read()
    git_object = GIT_OBJECT_TYPE_TO_CLASS.get(object_type, None)
    if git_object is None:
      raise InvalidObjectType("Object type {} is not one of {}".format(object_type, GIT_OBJECT_TYPES)) 
    else:
      git_object = git_object(repo, data)
      git_object.initialize()
      return write_object(git_object, write=write)

def find_object(repo, name, object_type=None, follow=True):
  return name

def generate_graphviz_log(repo, sha, logger, seen=set()):
  if sha in seen:
    return
  seen.add(sha)
  commit = read_object(repo, sha)
  assert(commit.object_type == "commit")

  parents = commit.data.get(b"parent", [])
  # Check if it is the first commit.
  if len(parents) == 0:
    logger.echo("c_{}".format(sha))
    return
  for parent in parents:
    decoded_parent = parent.decode("ascii")
    logger.echo("c_{} -> c_{}".format(sha, decoded_parent))
    generate_graphviz_log(repo, decoded_parent, logger, seen=seen)

def checkout_tree(repo, git_tree, path):
  for node in git_tree.data:
    git_object = read_object(repo, node.sha)
    destination = os.path.join(path, node.path)

    if git_object.object_type == "tree":
      os.mkdir(destination)
      checkout_tree(repo, git_object, destination)
    elif git_object.object_type == "blob":
      with open(destination, "wb") as blob:
        blob.write(git_object.data)
    