import math

import xenon_exceptions as xe
import params

class XenonObj(object):
  """ Base class for any object defined by the Xenon system. """
  def __init__(self):
    pass

class Param(XenonObj):
  def __init__(self, name, default):
    # Name of the attribute to set in an XenonObj.
    self.name = name
    self.default = default

  def __eq__(self, other):
    if type(self) == type(other):
      return self.name == other.name
    elif isinstance(other, str):
      return self.name == other
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __repr__(self):
    return "{0}(\"{1}\",{2})".format(self.__class__.__name__, self.name, self.default)

class Sweepable(XenonObj):
  """ Base class for any object with parameters that can be swept. """
  # A list of sweepable parameters for this class.
  sweepable_params = []

  def __init__(self, name):
    self.name = name
    # The command `sweep param from x to y linstep z` will check if `param` is
    # an entry of sweepable_params for this class. If so, it add an entry to
    # this dict, mapping name to the specified range (which is immediately
    # expanded into a Python list).
    self.sweep_params_range = {}
    self.createSweepAttributes()

  def createSweepAttributes(self):
    """ Create an attribute for each parameter in sweepable_params. """
    for param in self.__class__.sweepable_params:
      setattr(self, param.name, param.default)

  def setSweepParameter(self, name, start, end, step, step_type):
    if not name in self.__class__.sweepable_params:
      return xe.INVALID_SWEEP_PARAMETER
    if (step_type != "linstep" and step_type != "expstep"):
      raise xe.XenonInvalidStepTypeError(name, step_type)
    if (step_type == "linstep" and step == 0) or (step_type == "expstep" and step == 1):
      raise xe.XenonInvalidStepAmountError(name, step, step_type)

    value_range = []
    if step_type == "linstep":
      value_range = range(start, end+1, step)
    elif step_type == "expstep":
      value_range = [start * (step ** exp)
                     for exp in range(0, int(math.log(end/start, step))+1)]
    self.sweep_params_range[name] = value_range
    return xe.SUCCESS

class DesignSweep(Sweepable):
  sweepable_params = Sweepable.sweepable_params + []

  def __init__(self, name=None, sweep_type=None):
    super(DesignSweep, self).__init__(name)
    self.sweep_type = sweep_type  # TODO Support different sweep types.
    self.generate_outputs = set()
    self.done = False

    # Global settings about this sweep.
    self.output_dir = ""
    self.source_dir = ""
    self.memory_type = ""
    self.simulator = ""

  def __iter__(self):
    for key in self.__dict__:
      yield key

  def initializeSweep(self, name, sweep_type):
    self.name = name
    self.sweep_type = sweep_type

  def endSweep(self):
    self.checkInitializedAndRaise_()
    self.done = True

  def addGenerateOutput(self, output):
    self.checkInitializedAndRaise_()
    self.generate_outputs.add(output)

  def checkInitializedAndRaise_(self):
    if self.name == None:
      raise xe.SweepNotInitializedError()

  def __repr__(self):
    return "{0}(\"{1}\",{2})".format(self.__class__.__name__, self.name, self.sweep_type)
