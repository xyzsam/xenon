class SweepNotInitializedError(Exception):
  def __init__(self):
    super(SweepNotInitializedException, self).__init__(
        "Sweep has not been initialized with a begin statement.")

class XenonImportError(Exception):
  def __init__(self, package_path):
    super(XenonImportError, self).__init__(
        "Failed to import package path %s" % package_path)
