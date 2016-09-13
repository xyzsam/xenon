import xenon_exceptions as xe

class XenonObj(object):
  """ Base class for any object defined by the Xenon system. """
  def __init__(self):
    pass

class Sweepable(XenonObj):
  """ Base class for any object with parameters that can be swept. """
  # A list of sweepable parameters for this class.
  sweepable_params_ = []

  def __init__(self, name):
    self.name = name
    # The command `sweep param from x to y linstep z` will check if `param` is
    # an entry of sweepable_params for this class. If so, it add an entry to
    # this dict, mapping name to the specified range (which is immediately
    # expanded into a Python list).
    self.sweep_params_ = {}

  def setSweepParameter(self, name, start, end, step, step_type):
    if not name in sweepable_params_:
      raise xe.XenonInvalidSweepParameterError(name, self)

    value_range = []
    if step_type == "linstep":
      value_range = range(start, end+1, step)
    elif step_type == "expstep":
      value_range = [start * (step ** exp)
                     for exp in range(0, int(math.log(end/start, step))+1)]
    else:
      raise xe.XenonInvalidStepTypeError(name, step_type)
    self.sweep_params_[name] = value_range

class DesignSweep(Sweepable):
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
    return "DesignSweep({0},{1})".format(self.name, self.sweep_type)