import itertools
import math
import pprint
from types import *

from xenon.base.parsers import *
import xenon.base.exceptions as xe

class XenonObj(object):

  """ Base class for any object defined by the Xenon system. """
  def __init__(self):
    pass

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
    attr_value = getattr(self, attr)
    return not attr.startswith("__") and isinstance(attr_value, objtype)

class Param(XenonObj):
  """ An attribute that can be set via a Xenon set command.

  Parameters are described by a name, default value, and an automatically
  generated unique identifer. They are distinguished by id. Changing the
  id field of a parameter lets it be identified as a distinct attribute regardless
  of its name, so it can be swept independently.

  TODO: This needs to be clarified - parameters in different objects with the
  same id can have different values; they will just be swept jointly.
  """
  # Monotonically increasing id for all newly created Params.
  #
  # We use this instead of a random id so that we can guarantee stability in
  # generated configs; that is, as long as the Xenon input file does not
  # change, then we should generate the exact same configurations in the exact
  # same order every time. This greatly simplifies testing.
  next_id_ = itertools.count().next

  def __init__(self, name, default):
    super(Param, self).__init__()
    self.id = Param.next_id_()
    self.name = name
    self.default = default

  def __eq__(self, other):
    if type(self) == type(other):
      return self.id == other.id
    elif isinstance(other, str):
      # This is used by the BaseSweepable.setSweepParameter function.
      return self.name == other
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __str__(self):
    return "{0}(\"{1}\")".format(self.__class__.__name__, self.name)

  def __repr__(self):
    return "{0}(\"{1}\",{2})".format(self.__class__.__name__, self.name, self.default)

class BaseSweepable(XenonObj):
  """ Base class for any object with parameters that can be swept. """
  # A list of sweepable parameters for this class.
  # TODO: If we want to sweep parameters of the same name independently, that
  # would be a per-instance difference, so this should be part of the instance.
  sweepable_params = []

  def __init__(self, name):
    super(BaseSweepable, self).__init__()
    self.name = name

    # Automatically generated mapping to/from Param name and id.
    # TODO: Does this actually provide any significant benefit compared to
    # iterating over sweepable_params list?
    self.sweepable_params_dict_ = {}

    # The command `sweep param from x to y linstep z` will check if `param` is
    # an entry of sweepable_params for this class. If so, it add an entry to
    # this dict, mapping the parameter id to the specified range (which is
    # immediately expanded into a Python list).
    self.sweep_params_range_ = {}
    self.createSweepAttributes()

  def createSweepAttributes(self):
    """ Create an attribute for each parameter in sweepable_params. """
    for param in self.__class__.sweepable_params:
      # Setting the value to None by default (instead of param.default) makes
      # it possible to distinguish values that should be inherited from this
      # object's parents from values that were specifically set on this object
      # by the user.
      setattr(self, param.name, None)
      # TODO: This is a BUG that would result from having independent
      # parameters with the same name but different ids! Ensure that each
      # Sweepable has uniquely distinct param names.
      self.sweepable_params_dict_[param.name] = param.id
      self.sweepable_params_dict_[param.id] = param.name

  def getParamDefaultValue(self, name):
    for param in self.__class__.sweepable_params:
      if param.name == name:
        return param.default
    return None

  def getParamId(self, name):
    if name in self.sweepable_params_dict_:
      return self.sweepable_params_dict_[name]
    return None

  def getParamName(self, param_id):
    return self.sweepable_params_dict_[param_id]

  def hasSweepParamRange(self, name):
    param_id = self.getParamId(name)
    return param_id in self.sweep_params_range_

  def getSweepParamRange(self, name_or_id):
    if isinstance(name_or_id, str):
      param_id = self.getParamId(name_or_id)
    else:
      param_id = name_or_id
    return self.sweep_params_range_[param_id]

  def removeFromSweepParamRange(self, name):
    param_id = self.getParamId(name)
    del self.sweep_params_range_[param_id]

  def iterparamids(self):
    """ Returns a generator over ids of swept parameters. """
    return self.sweep_params_range_.iterkeys()

  def iterparamitems(self):
    """ Returns a generator over ids and ranges of swept parameters. """
    return self.sweep_params_range_.iteritems()

  def setSweepParameter(self, name, start, end, step, step_type):
    """ Sets the named sweep parameter with the given range.

    Returns:
      INVALID_SWEEP_PARAMETER: if this parameter is not sweepable.
      SUCCESS: otherwise.

    Throws:
      XenonInvalidStepTypeError: if step_type is not recognized.
      XenonInvalidStepAmountError: if the step amount would produce an invalid range.
    """
    if (step_type != KW_LINSTEP and step_type != KW_EXPSTEP):
      raise xe.XenonInvalidStepTypeError(name, step_type)
    if (step_type == KW_LINSTEP and step == 0) or (step_type == KW_EXPSTEP and step == 1):
      raise xe.XenonInvalidStepAmountError(name, step, step_type)
    param_id = self.getParamId(name)
    if param_id == None:
      return xe.INVALID_SWEEP_PARAMETER

    value_range = []
    if step_type == "linstep":
      value_range = range(start, end+1, step)
    elif step_type == "expstep":
      value_range = [start * (step ** exp)
                     for exp in range(0, int(math.log(end/start, step))+1)]
    self.sweep_params_range_[param_id] = value_range
    return xe.SUCCESS

  def getSweepableParams(self):
    """ Returns the list of sweepable parameters for this class. """
    return self.__class__.sweepable_params

  def getSweepableParamsAndValues(self):
    """ Returns a dict of parameter (name, value) for all sweepable parameters. """
    # TODO: Consider making this part of XenonObj.iterattr*
    return dict((p.name, getattr(self, p.name)) for p in self.getSweepableParams())

  def dump(self):
    """ Dumps all sweepable parameters in a readable format.

    This is only meant for debugging purposes.
    """
    dictified = self.dictify()
    printer = pprint.PrettyPrinter(indent=2)
    printer.pprint(dictified)

  def dictify(self):
    """ Generate a dict representation of this object.

    This representation only includes sweepable parameters and objects.
    """
    # First, generate the sweepable params and their values.
    key = str(self)
    set_params = self.getSweepableParamsAndValues()
    for param in set_params.iterkeys():
      if self.hasSweepParamRange(param):
        set_params[param] = self.getSweepParamRange(param)
    output = set_params

    # Now, repeat for each BaseSweepable attribute.
    attrs = self.iterattrkeys(objtype=BaseSweepable)
    for attr in attrs:
      output[attr] = getattr(self, attr).dictify()
    return {key: output}

  def __str__(self):
    return "{0}(\"{1}\")".format(self.__class__.__name__, self.name)

  def __repr__(self):
    return "{0}(name=\"{1}\",id={2})".format(self.__class__.__name__, self.name, self.id)

class Sweepable(BaseSweepable):
  """ Public Sweepable interface.

  All user objects that need to be swept should inherit from Sweepable (and not
  BaseSweepable). This is because Sweepable will track certain attributes that
  user objects have added on top of BaseSweepable. This allows the Xenon
  system to distinguish between internal attributes and attributes that should
  appear in any generated output files.

  User attributes are tracked in a set called "user_attrs". Only built-in types
  are tracked by this set; user-defined classes are ignored. Also, any
  attribute beginning or ending with "_" is ignored; this lets users implement
  private variables without having them appear in the generated output.
  """

  builtins_ = [IntType, FloatType, StringType, DictType, ListType,
               BooleanType, LongType, ComplexType, TupleType, UnicodeType]

  def __init__(self, name):
    # We must add the user_attrs attribute before calling the super
    # constructor, since the super constructor will also eventually call
    # __setattr__, which expects the presence of user_attrs.
    self.user_attrs = set()
    super(Sweepable, self).__init__(name)

  def __setattr__(self, attr, value):
    self.__dict__[attr] = value
    if (type(value) in Sweepable.builtins_ and
        not attr.startswith("_") and
        not attr.endswith("_") and
        not attr == "user_attrs"):
      self.user_attrs.add(attr)

class DesignSweep(Sweepable):
  sweepable_params = []

  def __init__(self, name=None, sweep_type=None):
    super(DesignSweep, self).__init__(name)
    self.sweep_type = sweep_type  # TODO Support different sweep types.
    self.generate_outputs = set()
    self.done_ = False

    # Global settings about this sweep.
    self.output_dir = ""
    self.source_dir = ""
    self.memory_type = ""
    self.simulator = ""

  def initializeSweep(self, name, sweep_type):
    self.name = name
    self.sweep_type = sweep_type

  def endSweep(self):
    self.checkInitializedAndRaise_()
    self.done_ = True

  def isDone(self):
    return self.done_

  def addGenerateOutput(self, output):
    self.checkInitializedAndRaise_()
    self.generate_outputs.add(output)

  def checkInitializedAndRaise_(self):
    if self.name == None:
      raise xe.SweepNotInitializedError()

  def __repr__(self):
    return "{0}(\"{1}\",{2})".format(self.__class__.__name__, self.name, self.sweep_type)
