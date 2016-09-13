class XenonError(Exception):
  def __init__(self, msg):
    super(XenonError, self).__init__(msg)

class SweepNotInitializedError(XenonError):
  def __init__(self, msg):
    super(SweepNotInitializedException, self).__init__(
        "Sweep has not been initialized with a begin statement.")

class XenonImportError(XenonError):
  def __init__(self, package_path):
    super(XenonImportError, self).__init__(
        "Failed to import package %s" % package_path)

class XenonSelectionError(XenonError):
  def __init__(self, selection_path):
    super(XenonSelectionError, self).__init__(
        "Failed to find object named %s" % selection_path)

class XenonInvalidStepTypeError(XenonError):
  def __init__(self, param_name, step_type):
    super(XenonInvalidStepTypeError, self).__init__(
        "Parameter %s has invalid step type %s" % (param_name, step_type))

# TODO: Consider removing this exception class.
class XenonInvalidSweepParameterError(XenonError):
  def __init__(self, parameter, instance):
    super(XenonInvalidSweepParameterError, self).__init__(
        "Parameter %s cannot be swept on object of type %s" % (
            parameter, type(instance).__name__))

class NotXenonObjError(XenonError):
  def __init__(self, obj):
    super(NotXenonObjError, self).__init__("%s is not of type XenonObj.")
