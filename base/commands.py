import abc
import copy
import importlib
import pyparsing as pp
from pydoc import locate

from xenon.base.datatypes import XenonObj, Sweepable, UnassignedParamValue
from xenon.base.exceptions import *
from xenon.base.expressions import Expression
from xenon.base.keywords import *
import xenon.base.common as common
import xenon.base.globalscope as g

class Command(XenonObj):
  """ Commands describe an action to perform on a sweep.

  Subclasses must implement the execute method, which can take an arbitrary
  number of arguments. Generally, all that is required is a DesignSweep object, as
  it should encapsulate all the state needed.

  Commands can be invoked using operator() like command(sweep_obj), for
  brevity. This is equivalent to calling execute().
  """
  __metaclass__ = abc.ABCMeta

  def __init__(self, lineno, line, parse_result):
    # Line number in the Xenon file.
    self.lineno = lineno
    # Original raw command.
    self.line = line
    # Keep a copy of the original parsed result around.
    self.parse_result = parse_result

  @abc.abstractmethod
  def execute(self, *args):
    pass

  def __call__(self, *args):
    return self.execute(*args)

  def __repr__(self):
    return self.line

class SelectionCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ Constructs a selection argument given a set of parsed tokens. """
    super(SelectionCommand, self).__init__(lineno, line, parse_result.selection)
    self.parse_result = parse_result
    self.tokens = list(parse_result.selection)

  def select(self, env):
    """ Return a list of objects in an environment selected by this selection.

    See common.select() for more details.
    """
    return common.getSelectedObjs(self.tokens, env)

  def execute(self, env):
    return self.select(env)

class BeginCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ Begin command specifies sweep name and sweep type. """
    super(BeginCommand, self).__init__(lineno, line, parse_result)
    self.name = parse_result.sweep_name
    self.sweep_class_name = parse_result.sweep_class

  def findSweepClassType(self):
    """ Return the type by the name sweep_class_name.

    Search in either xenon.base.datatypes or in Xenon global scope.

    Returns:
      A type of type BaseDesignSweep if found, None otherwise.
    """
    internal_path = "xenon.base.designsweeptypes.%s" % self.sweep_class_name
    SweepClassType = locate(internal_path)
    if SweepClassType:
      return SweepClassType
    global_path = "xenon.base.globalscope.scope.%s" % self.sweep_class_name
    SweepClassType = locate(global_path)
    if SweepClassType:
      return SweepClassType
    return None

  def execute(self, sweep_obj):
    assert(sweep_obj == None)
    # Try to construct this sweep object from local scope.
    SweepClassType = self.findSweepClassType()
    if not SweepClassType:
      raise XenonTypeError("Unknown sweep type {}.".format(self.sweep_class_name))
    sweep_obj = SweepClassType(self.name)
    sweep_obj.initializeSweep(self.name)
    return sweep_obj

class EndCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ End command contains no additional information. """
    super(EndCommand, self).__init__(lineno, line, parse_result)

  def execute(self, sweep_obj):
    sweep_obj.endSweep()
    return sweep_obj

class SetCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ Construct a set command.

    A set command's value can be either a constant numeric value, a string, or
    an expression.
    """
    super(SetCommand, self).__init__(lineno, line, parse_result)
    self.param = parse_result.param
    self.selection = SelectionCommand(lineno, line, parse_result)
    if len(parse_result.constant):
      self.value = int(parse_result.constant)
    elif len(parse_result.string):
      self.value = parse_result.string
    elif len(parse_result.list):
      self.value = list(parse_result.list)
    else:
      self.value = parse_result.expression

  def setParam(self, sweep_obj):
    """ Set the parameter on all the selected objects to the provided value.

    The selected objects are taken from sweep_obj, the current sweep.

    The syntax purposely allows for * to select all members of an object, even
    ones that do not have this parameter. If, after going through all selected
    objects, none have the parameter as an attribute, raise an exception.

    Expressions can naturally refer to attributes of other Sweepable objects,
    but there are a few ways they can be written, so we attempt to evaluate
    them in three places.
      1. Evaluate it using the sweep object as the top level scope.
      2. Evaluate it during config generation time. This covers scenarios where the
         expression depends on the value of a swept parameter.
    """
    value = self.value
    if isinstance(value, Expression):
      try:
        # Attempt to evaluate the expression with at sweep scope.
        value = self.value.eval(sweep_obj)
      except XenonTypeError as e:
        # If we fail because of an unassigned parameter, try again during sweep
        # generation.
        value = self.value
      except XenonSelectionError as e:
        # If the selection failed, then don't do anything.
        value = UnassignedParamValue()

    selected_objs = self.selection(sweep_obj)
    is_applied = False
    for obj in selected_objs:
      if hasattr(obj, self.param):
        if not isinstance(value, UnassignedParamValue):
          setattr(obj, self.param, value)
        is_applied = True
        # Remove this parameter from obj.sweep_params_range, if it exists, so
        # that the sweep generator ignores this value. Note, however, that a
        # sweep command after the set command can restore this parameter to
        # sweep_params_range!
        if isinstance(obj, Sweepable) and obj.hasSweepParamRange(self.param):
          obj.removeFromSweepParamRange(self.param)

    if not is_applied:
      raise XenonEmptySelectionError(self.param)

  def execute(self, sweep_obj):
    self.setParam(sweep_obj)
    return sweep_obj

class UseCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(UseCommand, self).__init__(lineno, line, parse_result)
    self.package_path = list(parse_result.package_path)

  def execute(self, sweep_obj):
    target_obj = sweep_obj if sweep_obj else g.scope
    # The last identifer of the path could be either a module or a member of a
    # module, so always start by importing the parent. In the case that there
    # is only one identifier to the path, then that path is the parent.
    if len(self.package_path) > 2:
      path_terminator = self.package_path[-1]
      parent_module_path = ".".join(self.package_path[:-1])
    else:
      path_terminator = ""
      parent_module_path = ".".join(self.package_path)

    try:
      parent_package = importlib.import_module(parent_module_path)
    except ImportError as e:
      raise XenonImportError(self.package_path, e)

    if path_terminator == LIT_STAR:
      # Import everything into the global namespace.
      for attr, val in parent_package.__dict__.items():
        if isinstance(val, XenonObj) or isinstance(val, type):
          target_obj.__dict__[attr] = copy.deepcopy(val)
    elif path_terminator != "":
      # Import the specified child item (which might be module itself).
      try:
        target_obj.__dict__[path_terminator] = getattr(parent_package, path_terminator)
      except AttributeError as e:
        raise XenonImportError(self.package_path, e)
    else:
      # There was no child specified for this path.
      target_obj.__dict__[parent_module_path] = parent_package

    return sweep_obj

class SourceCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(SourceCommand, self).__init__(lineno, line, parse_result)
    self.source_file = parse_result.source_file

  def execute(self, sweep_obj):
    raise XenonError("A source command should never be executed here.")

class GenerateCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(GenerateCommand, self).__init__(lineno, line, parse_result)
    self.target = parse_result.target

  def execute(self, sweep_obj):
    sweep_obj.addGenerateOutput(self.target)
    return sweep_obj

class SweepCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(SweepCommand, self).__init__(lineno, line, parse_result)
    if parse_result.range:
      self.is_explicit_list = False
      self.sweep_start = int(parse_result.range.start)
      self.sweep_end = int(parse_result.range.end)
      self.step = int(parse_result.range.step.amount)
      self.step_type = parse_result.range.step.type
    elif parse_result.list:
      self.is_explicit_list = True
      self.list_value = parse_result.list
    self.sweep_param = parse_result.sweep_param
    self.selection = SelectionCommand(lineno, line, parse_result)

  def execute(self, sweep_obj):
    selected_objs = self.selection(sweep_obj)
    is_applied_at_least_once = False
    for obj in selected_objs:
      if not isinstance(obj, Sweepable):
        continue
      if self.is_explicit_list:
        ret = obj.setSweepParameterList(self.sweep_param, self.list_value)
      else:
        ret = obj.setSweepParameter(
            self.sweep_param, self.sweep_start, self.sweep_end,
            self.step, self.step_type)
      if ret == SUCCESS:
        is_applied_at_least_once = True

    if not is_applied_at_least_once:
      raise XenonEmptySelectionError(self.sweep_param)
    return sweep_obj
