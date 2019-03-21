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
    for key, values in dictionary.items():
      if key == b"message":
        continue
      for value in values:
        builder += "{key}{space}{value}{newline}".format(key=key,
                                                        space=b" ",
                                                        value=value.replace(b"\n", b"\n "),
                                                        newline=b"\n")
    builder += "\n" + "".join(dictionary[b"message"])
    return builder

class GitCommit(GitObject):
  def __init__(self, repo, raw_data=None):
    super().__init__(repo, raw_data)
    self.message_parser = MessageParser()
  
  def serialize(self):
    return self.message_parser.serialize_git_message(self.data)

  def deserialize(self):
    return self.message_parser.parse_git_message(self.raw_data)


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
