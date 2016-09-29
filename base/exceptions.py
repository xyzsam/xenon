# Error codes.
SUCCESS = 0
INVALID_SWEEP_PARAMETER = 1

# Exception classes.
class XenonError(Exception):
  def __init__(self, msg):
    super(XenonError, self).__init__(msg)

class SweepNotInitializedError(XenonError):
  def __init__(self):
    super(SweepNotInitializedError, self).__init__(
        "Sweep has not been initialized with a begin statement.")

class XenonImportError(XenonError):
  def __init__(self, package_path, import_err):
    super(XenonImportError, self).__init__(
        "Failed to import package %s because: %s" % (package_path, str(import_err)))

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

class XenonEmptySelectionError(XenonError):
  def __init__(self, attr):
    super(XenonEmptySelectionError, self).__init__(
        "No objects with sweepable attribute \"%s\" were found." % attr)

class XenonMismatchingRangeError(XenonError):
  def __init__(self, param_name, this_length, prev_length):
    super(XenonMismatchingRangeError, self).__init__(
        "Parameter %s has sweep range of length %d, which is not equal to a previous "
        "sweep command on this parameter with a sweep range of length %d." %
        (param_name, this_length, prev_length))
    self.param_name = param_name
    self.this_length = this_length
    self.prev_length = prev_length

class XenonTypeError(XenonError):
  def __init__(self, msg):
    super(XenonTypeError, self).__init__(msg)

class DuplicateSweepNameError(XenonError):
  def __init__(self, sweep_name):
    super(DuplicateSweepNameError, self).__init__(
        "%s was already declared as the name of another sweep." % sweep_name)
