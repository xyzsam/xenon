# Error codes.
SUCCESS = 0
INVALID_SWEEP_PARAMETER = 1

# Exception classes.
class XenonError(Exception):
  def __init__(self, msg):
    super(XenonError, self).__init__(msg)

# TODO: Get rid of this error.
class XenonSyntaxError(XenonError):
  def __init__(self, parser_err, lineno):
    super(XenonSyntaxError, self).__init__("")
    self.parser_err = parser_err

  def __str__(self):
    spaces =  ' ' * (self.parser_err.col - 1)
    msg = "Invalid syntax\n"
    msg += "  ", self.parser_err.line
    msg += "   %s^" % spaces
    msg += str(err)

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

class XenonInvalidStepAmountError(XenonError):
  def __init__(self, name, step, step_type):
    super(XenonInvalidStepAmountError, self).__init__(
        "Sweep range %s with step type %s cannot have step amount %d" % (name, step_type, step))

class XenonInvalidStepTypeError(XenonError):
  def __init__(self, param_name, step_type):
    super(XenonInvalidStepTypeError, self).__init__(
        "Parameter %s has invalid step type %s" % (param_name, step_type))

class NotXenonObjError(XenonError):
  def __init__(self, obj):
    super(NotXenonObjError, self).__init__("%s is not of type XenonObj.")

class XenonAttributeError(XenonError):
  def __init__(self, attr):
    super(XenonAttributeError, self).__init__(
        "No objects with sweepable attribute %s were found." % attr)
