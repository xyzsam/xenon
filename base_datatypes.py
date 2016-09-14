import math
import pprint
import uuid

import xenon_exceptions as xe

class XenonObj(object):
  """ Base class for any object defined by the Xenon system. """
  def __init__(self):
    # Unique identifier for all Xenon objects.
    self.id = uuid.uuid1().int

  def iterattrkeys(self, objtype=object):
    """ Analogue of dict.iterkeys() over attributes, with filtering. """
    for attr in dir(self):
      if self.filter_func_(attr, objtype):
        yield attr

  def iterattrvalues(self, objtype=object):
    """ Analogue of dict.itervalues() over attributes, with filtering. """
    for attr in self.iterattrkeys(objtype=objtype):
      yield getattr(self, attr)

  def iterattritems(self, objtype=object):
    """ Analogue of dict.iteritems() over attributes, with filtering. """
    for attr in self.iterattrkeys(objtype=objtype):
      yield attr, getattr(self, attr)

  def filter_func_(self, attr, objtype):
    """ Returns true if the attribute is not a builtin and optionally is of the given type. """
    return not attr.startswith("__") and isinstance(getattr(self, attr), objtype)

class Param(XenonObj):
  """ An attribute that can be set via a Xenon set command.

  Parameters are described by a name, default value, and an automatically
  generated unique identifer. They are distinguished by id. Changing the
  id field of a parameter lets it be identified as a distinct attribute regardless
  of its name, so it can be swept independently.
  """
  def __init__(self, name, default):
    super(Param, self).__init__()
    self.name = name
    self.default = default

  def __eq__(self, other):
    if type(self) == type(other):
      return self.id == other.id
    elif isinstance(other, str):
      # This is used by the Sweepable.setSweepParameter function.
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

  # Automatically generated mapping from Param name to id.
  sweepable_params_dict_ = {}

  def __init__(self, name):
    self.name = name
    # The command `sweep param from x to y linstep z` will check if `param` is
    # an entry of sweepable_params for this class. If so, it add an entry to
    # this dict, mapping the parameter id to the specified range (which is
    # immediately expanded into a Python list).
    self.sweep_params_range = {}
    self.createSweepAttributes()

  def createSweepAttributes(self):
    """ Create an attribute for each parameter in sweepable_params. """
    for param in self.__class__.sweepable_params:
      # Setting the value to None by default (instead of param.default) makes
      # it possible to distinguish values that should be inherited from this
      # object's parents from values that were specifically set on this object
      # by the user.
      setattr(self, param.name, None)
      self.__class__.sweepable_params_dict_[param.name] = param.id

  def getParamId(self, name):
    return self.__class__.sweepable_params_dict_[name]

  def hasSweepParamRange(self, name):
    param_id = self.getParamId(name)
    return param_id in self.sweep_params_range

  def getSweepParamRange(self, name):
    param_id = self.getParamId(name)
    return self.sweep_params_range[param_id]

  def setSweepParameter(self, name, start, end, step, step_type):
    """ Sets the named sweep parameter with the given range.

    Returns:
      INVALID_SWEEP_PARAMETER: if this parameter is not sweepable.
      SUCCESS: otherwise.

    Throws:
      XenonInvalidStepTypeError: if step_type is not recognized
      XenonInvalidStepAmountError: if the step amount would produce an invalid range.
    """
    if (step_type != "linstep" and step_type != "expstep"):
      raise xe.XenonInvalidStepTypeError(name, step_type)
    if (step_type == "linstep" and step == 0) or (step_type == "expstep" and step == 1):
      raise xe.XenonInvalidStepAmountError(name, step, step_type)
    if not name in self.__class__.sweepable_params_dict_:
      return xe.INVALID_SWEEP_PARAMETER

    param_id = self.getParamId(name)
    value_range = []
    if step_type == "linstep":
      value_range = range(start, end+1, step)
    elif step_type == "expstep":
      value_range = [start * (step ** exp)
                     for exp in range(0, int(math.log(end/start, step))+1)]
    self.sweep_params_range[param_id] = value_range
    return xe.SUCCESS

  def dump(self):
    """ Dumps all sweepable parameters in a readable format.

    This is only meant for debugging purposes.
    """
    dictified = self.dictify()
    printer = pprint.PrettyPrinter(indent=4)
    printer.pprint(dictified)

  def dictify(self):
    """ Generate a dict representation of this object.

    This representation only includes sweepable parameters and objects.
    """
    # First, generate the sweepable params and their values.
    key = str(self)
    set_params = dict((p.name, getattr(self, p.name)) for p in self.__class__.sweepable_params)
    set_params.update(self.sweep_params_range)
    output = set_params

    # Now, repeat for each Sweepable attribute.
    attrs = self.iterattrkeys(objtype=Sweepable)
    for attr in attrs:
      output[attr] = getattr(self, attr).dictify()
    return output

  def __repr__(self):
    return "{0}(name=\"{1}\",id={2})".format(self.__class__.__name__, self.name, self.id)

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

  # TODO: Deprecated?
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
