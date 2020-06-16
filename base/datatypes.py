import itertools
import math
import pprint

from xenon.base.keywords import *
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
  id_ = itertools.count()

  def __init__(self, expected_type, name, default, valid_opts=None, format_func=None):
    super(Param, self).__init__()
    self.id = next(Param.id_)
    self.name = name
    self.default = default
    self.valid_opts = valid_opts
    # An optional function to run to return a string formatted version of this
    # parameter's value.
    self.format_func = format_func
    self.expected_type = expected_type

    # TODO: Add unit tests for validation.
    if not isinstance(self.default, expected_type):
      raise TypeError(
          "Expected default value {0} of {1} {2} to be {3}.".format(
              self.default, self.__class__.__name__, self.name, expected_type))

    if not self.valid_opts:
      return

    for opt in self.valid_opts:
      if not isinstance(opt, expected_type):
        raise TypeError("Expected valid option {0} of {1} {2} to be {3}.".format(
            opt, self.__class__.__name__, self.name, expected_type))

  def format(self, value):
    """ Returns a string representation of this value.

    Returns:
      format_func(value) if format_func was specified; otherwise, str(value).
    """
    if self.format_func:
      return self.format_func(value)
    return str(value)

  def validate(self, value):
    """ Checks whether this value is one of the valid options.

    If this value is not valid, raise the appropriate Error; otherwise, return.
    """
    if not self.valid_opts:
      return
    if isinstance(value, UnassignedParamValue):
      return
    if not value in self.valid_opts:
      raise ValueError(
          "Value {0} is not a valid option for {1} {2}. "
          "Valid options are: {3}".format(
              value, self.__class__.__name__, self.name, self.valid_opts))

  def __eq__(self, other):
    if type(self) == type(other):
      return self.id == other.id
    elif isinstance(other, str):
      # This is used by the Sweepable.setSweepParameter function.
      return self.name == other
    return False

  def __ne__(self, other):
    return not self.__eq__(other)

  def __str__(self):
    return "{0}(\"{1}\")".format(self.__class__.__name__, self.name)

  def __repr__(self):
    return "{0}(\"{1}\",{2})".format(self.__class__.__name__, self.name, self.default)

# Convenience classes for different types of parameters.
class IntParam(Param):
  def __init__(self, *args, **kwargs):
    super(IntParam, self).__init__(int, *args, **kwargs)

class StrParam(Param):
  def __init__(self, *args, **kwargs):
    super(StrParam, self).__init__(str, *args, **kwargs)

class BoolParam(Param):
  def __init__(self, *args, **kwargs):
    super(BoolParam, self).__init__(bool, *args, **kwargs)

class UnassignedParamValue(XenonObj):
  """ An object to represent a Param attribute without a value.

  Attempting to convert this object into a float or int will raise a
  XenonTypeError.  This is preferable to assigning None to unassigned values,
  since it is much more specific and less likely to happen on accident.
  """
  def __init__(self):
    super(UnassignedParamValue, self).__init__()

  def __float__(self):
    raise xe.XenonTypeError("UnassignedParamValue cannot be converted to float.")

  def __int__(self):
    raise xe.XenonTypeError("UnassignedParamValue cannot be converted to int.")

class Sweepable(XenonObj):
  """ Base class for any object with parameters that can be swept.

  User-defined classes for sweepable objects should subclass this and define
  sweepable_params and other attributes that need to appear in the output JSON.

  Sweepable will mark certain user-added attributes that user classes have
  added as attributes whose values must appear in the output JSON.  User
  attributes are tracked in a set called "user_attrs". Only built-in types are
  tracked by this set; user-defined classes are ignored. Also, any attribute
  beginning or ending with "_" is ignored; this lets users implement private
  variables without having them appear in the generated output.

  TODO: Expand this documentation.
  1. Explain when parameters should be initialized to None.
  2. Explain how attributes are handled.
  3. Distiguish sweepable_params from sweep_params_range_.
  """

  # A list of sweepable parameters for this class.
  # When a Sweepable object is constructed, this list is copied into the
  # constructed instance. All future references should use that list.
  # Per-instance lists can be modified, but this list cannot.
  sweepable_params = []

  builtins_ = [
      int, float, str, dict, list, None, bool, complex, tuple,
      UnassignedParamValue
  ]

  def __init__(self, name):
    # We must add the user_attrs attribute before calling the super
    # constructor, since the super constructor will also eventually call
    # __setattr__, which expects the presence of user_attrs.
    self.user_attrs = set()
    super(Sweepable, self).__init__()
    self.name = name

    self.sweepable_params_ = [p for p in self.__class__.sweepable_params]

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

  def __setattr__(self, attr, value):
    self.__dict__[attr] = value
    if (type(value) in Sweepable.builtins_ and
        not attr.startswith("_") and
        not attr.endswith("_") and
        not attr == "user_attrs"):
      self.user_attrs.add(attr)

  def createSweepAttributes(self):
    """ Create an attribute for each parameter in sweepable_params. """
    for param in self.sweepable_params_:
      # Setting the value to UnassignedParamValue by default (instead of
      # param.default) makes it possible to distinguish values that should be
      # inherited from this object's parents from values that were specifically
      # set on this object by the user.
      setattr(self, param.name, UnassignedParamValue())
      self.sweepable_params_dict_[param.name] = param.id
      self.sweepable_params_dict_[param.id] = param.name

  def removeSweepableParam(self, param):
    """ Remove the specified Param object from sweepable_params_. """
    self.sweepable_params_.remove(param)
    del self.sweepable_params_dict_[param.id]
    del self.sweepable_params_dict_[param.name]

  def getParamDefaultValue(self, name):
    for param in self.sweepable_params_:
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
    return self.sweep_params_range_

  def iterparamitems(self):
    """ Returns a generator over ids and ranges of swept parameters. """
    return self.sweep_params_range_.items()

  def setSweepParameter(self, name, start, end, step, step_type):
    """ Sets the named sweep parameter with the given range.

    Returns:
      INVALID_SWEEP_PARAMETER: if this object does not have this parameter, or
        if this parameter is not sweepable.
      SUCCESS: otherwise.

    Throws:
      XenonInvalidStepTypeError: if step_type is not recognized.
      XenonInvalidStepAmountError: if the step amount would produce an invalid range.
    """
    if (step_type != KW_LINSTEP and step_type != KW_EXPSTEP):
      raise xe.XenonInvalidStepTypeError(name, step_type)
    if (step_type == KW_LINSTEP and step == 0) or (step_type == KW_EXPSTEP and step == 1):
      raise xe.XenonInvalidStepAmountError(name, step, step_type)
    if (step_type == KW_EXPSTEP and (start == 0 or end == 0)):
      raise ValueError("Start/end of sweep range cannot be zero for exponential steps.")
    param_id = self.getParamId(name)
    if param_id == None:
      return xe.INVALID_SWEEP_PARAMETER

    value_range = []
    if step_type == "linstep":
      value_range = list(range(start, end + 1, step))
    elif step_type == "expstep":
      value_range = [start * (step ** exp)
                     for exp in range(0, int(math.log(end/start, step))+1)]
    self.sweep_params_range_[param_id] = value_range
    return xe.SUCCESS

  def setSweepParameterList(self, name, list_value):
    """ Sets the named sweep parameter to the provided list of values.

    Returns:
      INVALID_SWEEP_PARAMETER: if this object does not have this parameter, or
        if this parameter is not sweepable.
      SUCCESS: otherwise.
    """
    param_id = self.getParamId(name)
    if param_id == None:
      return xe.INVALID_SWEEP_PARAMETER
    self.sweep_params_range_[param_id] = list_value
    return xe.SUCCESS

  def getSweepableParamsAndValues(self):
    """ Returns a dict of parameter (name, value) for all sweepable parameters. """
    # TODO: Consider making this part of XenonObj.iterattr*
    return dict((p.name, getattr(self, p.name)) for p in self.sweepable_params_)

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
    for param in set_params:
      if self.hasSweepParamRange(param):
        set_params[param] = self.getSweepParamRange(param)
    output = set_params

    # Now, repeat for each Sweepable attribute.
    attrs = self.iterattrkeys(objtype=Sweepable)
    for attr in attrs:
      output[attr] = getattr(self, attr).dictify()
    return {key: output}

  def validate(self):
    """ Validate all child Sweepable objects and Params. """
    for obj in self.iterattrvalues(objtype=Sweepable):
      obj.validate()

    for param in self.sweepable_params_:
      param.validate(getattr(self, param.name))

  def __str__(self):
    return "{0}(\"{1}\")".format(self.__class__.__name__, self.name)

  def __repr__(self):
    return "{0}(name=\"{1}\")".format(self.__class__.__name__, self.name)

class BaseDesignSweep(Sweepable):
  sweepable_params = []

  def __init__(self, name=None):
    super(BaseDesignSweep, self).__init__(name)
    self.generate_outputs = set()
    self.done_ = False

    # Global settings about this sweep.
    self.output_dir = ""

  def validate(self):
    """ Raise an exception if this sweep has invalid attributes.

    Subclasses should override this method to implement their own validity
    checks.  However, they should still invoke this through super(). The base
    class only checks that a generate function exists for each generate output.
    """
    super(BaseDesignSweep, self).validate()
    for output in self.generate_outputs:
      generator_func_name = "generate_%s" % output
      if not hasattr(self, generator_func_name):
        raise AttributeError("%s has no method called %s" % (
            self.__class__.__name__, generator_func_name))
      if not callable(getattr(self, generator_func_name)):
        raise TypeError("%s.%s is not a function." % (
            self.__class__.__name__, generator_func_name))

  def initializeSweep(self, name):
    self.name = name

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

  def generateAllOutputs(self):
    all_genfiles = []
    for output in self.generate_outputs:
      func_name = "generate_%s" % output
      generator = getattr(self, func_name)
      genfiles = generator()
      all_genfiles.extend(genfiles)

    return all_genfiles

  def __repr__(self):
    return "{0}(\"{1}\")".format(self.__class__.__name__, self.name)
