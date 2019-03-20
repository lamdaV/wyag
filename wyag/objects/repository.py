import os
import configparser


class RepositoryInitializationError(Exception):
  pass


class Repository(object):
  def __init__(self, path, logger, force=False):
    self.worktree = path
    self.gitdir = os.path.join(path, ".git")
    self.force = force
    self.config = configparser.ConfigParser()
    self.logger = logger
      
  def repo_path(self, *path):
    """
    Returns the path joined to the Repository's gitdir.
    """
    return os.path.join(self.gitdir, *path)

  def repo_file(self, *path, mkdir=False):
    """
    Returns the joined paths. If mkdir is True, the paths will be created if possible. 
    Returns None otherwise.
    """
    if self.repo_dir(*path[:-1], mkdir=mkdir) is not None:
      return self.repo_path(*path)
    else:
      return None
  
  def repo_dir(self, *path, mkdir=False):
    """
    Returns the joined paths if it exists and is a directory or mkdir is True.
    Otherwise return None.

    Raises RepositoryInitializationError exception if path exists and is NOT a directory
    """
    repo_path = self.repo_path(*path)
    if os.path.exists(repo_path):
      if os.path.isdir(repo_path):
        return repo_path
      else:
        raise RepositoryInitializationError("Not a directory {}".format(repo_path))
    
    if mkdir:
      os.makedirs(repo_path)
      return repo_path
    else:
      return None

  def initialize(self):
    self.logger.info("initialize called with: {}".format(vars(self)))

    # If worktree exists, verify that it an EMPTY directory.
    # else, create an empty directory.
    self.logger.info("verifying if {}...".format(self.worktree))
    if os.path.exists(self.worktree):
      if not os.path.isdir(self.worktree):
        raise RepositoryInitializationError("{} is not a directory".format(self.worktree))
      elif len(os.listdir(self.worktree)) != 0:
        raise RepositoryInitializationError("{} is a non-empty directory".format(self.worktree))
    else:
      self.logger.info("creating directory(s) {}".format(self.worktree))
      os.makedirs(self.worktree)
    self.logger.info("verified worktree")

    # If not force, ensure that gitdir is ACTUALLY a directory
    self.logger.info("verifying if {}...".format(self.gitdir))
    if not (self.force or os.path.isdir(self.gitdir)):
      raise RepositoryInitializationError("Not a wyag repository {}".format(path))
    self.logger.info("verified {}".format(self.gitdir) if not self.force else "skipping gitdir verification")

    # Read config.
    self.logger.info("loading config...")
    config_file = self.repo_file("config")
    if config_file is not None and os.path.exists(config_file):
      self.config.read([config_file])
    elif not self.force:
      raise RepositoryInitializationError("Configuration file is missing")
    self.logger.info("loaded config" if not self.force else "skipping config load")
    
    # Verify repository format version
    if not self.force:
      self.info("verifying repository format version...")
      repository_format_version = int(self.config.get("core", "repositoryformatversion"))
      if repository_format_version != 0 and not self.force:
        raise RepositoryInitializationError("Unsupported repositoryformatversion {}".format(repository_format_version))
      self.info("verified repository format version")

    # Initialize .git directory
    self.logger.info("creating .git structure...")
    assert(self.repo_dir("branches", mkdir=True) is not None)
    assert(self.repo_dir("objects", mkdir=True) is not None)
    assert(self.repo_dir("refs", "tags", mkdir=True) is not None)
    assert(self.repo_dir("refs", "heads", mkdir=True) is not None)
    self.logger.info("created .git structure")

    # Initialize default files
    self.logger.info("writing default values for default .git files...")
    with open(self.repo_file("description"), "w") as description_file:
      description_file.write("Unnamed repository: edit this file 'description' to name the repository.\n")
    with open(self.repo_file("HEAD"), "w") as head_file:
      head_file.write("ref: refs/heads/master\n")
    with open(self.repo_file("config"), "w") as config_file:
      default_config = configparser.ConfigParser()
      default_config.add_section("core")
      default_config.set("core", "repositoryformatversion", "0")
      default_config.set("core", "filemode", "false")
      default_config.set("core", "bare", "false")
      default_config.write(config_file)
    self.logger.info("wrote default values for default .git files")

    self.logger.success("initialized git repo")


    