class XenonError(Exception):
  def __init__(self, msg):
    super(XenonError, self).__init__(msg)
    # self.msg = msg

class SweepNotInitializedError(XenonError):
  def __init__(self, msg):
    super(SweepNotInitializedException, self).__init__(
        "Sweep has not been initialized with a begin statement.")

class XenonImportError(XenonError):
  def __init__(self, package_path):
    super(XenonImportError, self).__init__(
        "Failed to import package path %s" % package_path)

class XenonSelectionError(XenonError):
  def __init__(self, selection_path):
    super(XenonSelectionError, self).__init__(
        "Failed to find object %s" % selection_path)
