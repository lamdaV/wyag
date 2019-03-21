import collections

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

class MessageParser(object):
  def parse_git_message(self, raw_data, start=0, dictionary=None):
    if dictionary is None:
      dictionary = collections.OrderedDict()
    
    space_index = raw_data.find(b" ", start)
    new_line_index = raw_data.find(b"\n", start)
    
    # If no space character was found or the new line character
    # appears before the space, assume this is a blank line
    # and the rest of the data is the message.
    if space_index < 0 or new_line_index < space_index:
      assert(new_line_index == start)
      dictionary[b"message"] = [raw_data[start + 1:]]
      return dictionary
    
    key = raw_data[start:space_index]

    # Find the end of the value by finding new line character not
    # followed by a space.
    end = start
    while True:
      end = raw_data.find(b"\n", end + 1)
      if raw_data[end + 1] != ord(" "):
        break

    value = raw_data[space_index + 1:end].replace(b"\n ", b"\n")
    mapped_value = dictionary.get(key, [])
    mapped_value.append(value)
    dictionary[key] = mapped_value
    
    return self.parse_git_message(raw_data, start=end+1, dictionary=dictionary)

  def serialize_git_message(self, dictionary):
    builder = b""
    messages = []
    for key, values in dictionary.items():
      if key == b"message":
        messages = values
        continue
      for value in values:
        builder += key + b" " + value.replace(b"\n", b"\n ") + b"\n"
        # builder += "{key}{space}{value}{newline}".format(key=key,
        #                                                  space=b" ",
        #                                                  value=value.replace(b"\n", b"\n "),
        #                                                  newline=b"\n").encode()
    builder += b"\n"
    builder += b"".join(messages)
    builder += b"\n"
    return builder

class GitCommit(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
    self.message_parser = MessageParser()
  
  def serialize(self):
    return self.message_parser.serialize_git_message(self.data)

  def deserialize(self):
    return self.message_parser.parse_git_message(self.raw_data)

class GitTreeNode(object):
  __slots__ = ["mode", "path", "sha"]

  def __init__(self, mode, path, sha):
    self.mode = mode
    self.path = path
    self.sha = sha

class TreeParser(object):
  def __init__(self):
    self.sha_length = 20

  def parse_one(self, raw_data, start=0):
    space_index = raw_data.find(b" ", start)
    
    # file mode
    assert(space_index - start == 5 or space_index - start == 6)
    mode = raw_data[start:space_index]

    # path
    null_index = raw_data.find(b"\x00", space_index)
    path = raw_data[space_index + 1:null_index]
    
    # due to inclusive-exclusive, include the last bit
    sha_end = null_index + self.sha_length + 1 
    sha = hex(int.from_bytes(raw_data[null_index + 1:sha_end], "big"))
    # hex constructs a string prefixed with 0x, drop that.
    sha = sha[2:]

    return sha_end, GitTreeNode(mode, path, sha)
  
  def parse(self, raw_data):
    position = 0
    end = len(raw_data)
    data = []
    while position < end:
      position, node = self.parse_one(raw_data, start=position)
      data.append(node)
    return data


class GitTree(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
    self.tree_parser = TreeParser()
  
  def serialize(self):
    return self.serialize_tree()

  def deserialize(self):
    return self.tree_parser.parse(self.raw_data)

  def serialize_tree(self):
    builder = b""
    for node in self.data:
      sha = int(node.sha, 16).to_bytes(20, byteorder="big")
      builder += "{mode}{space}{path}{null}{sha}".format(mode=node.mode,
                                                         space=b" ",
                                                         path=node.path,
                                                         null=b"\x00",
                                                         sha=sha)
    return builder

class GitTag(GitCommit):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)

GIT_OBJECT_TYPE_TO_CLASS = {
  "blob": GitBlob,
  "tree": GitTree,
  "tag": GitTag,
  "commit": GitCommit
}
GIT_CLASS_TO_OBJECT_TYPE = {git_class.__name__: git_type for git_type, git_class in GIT_OBJECT_TYPE_TO_CLASS.items()}
GIT_OBJECT_TYPES = [*GIT_OBJECT_TYPE_TO_CLASS]
