class GitObject(object):
  def __init__(self, repo, raw_data=None):
    # NOTE: repo may be None.
    self.repo = repo
    self.raw_data = raw_data
    self.data = None
    self.object_type = GIT_CLASS_TO_OBJECT_TYPE.get(type(self).__name__)
  
  def initialize(self):
    if self.data is None and self.raw_data is not None:
      self.data = self.deserialize()

  def serialize(self):
    raise NotImplementedError("serialize is not implemented")

  def deserialize(self):
    raise NotImplementedError("deserialize is not implemented")

class GitBlob(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
  
  def serialize(self):
    return self.data

  def deserialize(self):
    return self.raw_data

class GitCommit(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
  
  def serialize(self):
    return self.data

  def deserialize(self):
    return self.raw_data

class GitTree(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
  
  def serialize(self):
    return self.data

  def deserialize(self):
    return self.raw_data

class GitTag(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
  
  def serialize(self):
    return self.data

  def deserialize(self):
    return self.raw_data

GIT_OBJECT_TYPE_TO_CLASS = {
  "blob": GitBlob,
  "tree": GitTree,
  "tag": GitTag,
  "commit": GitCommit
}
GIT_CLASS_TO_OBJECT_TYPE = {git_class.__name__: git_type for git_type, git_class in GIT_OBJECT_TYPE_TO_CLASS.items()}
GIT_OBJECT_TYPES = [*GIT_OBJECT_TYPE_TO_CLASS]
