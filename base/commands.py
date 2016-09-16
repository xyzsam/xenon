import abc
import copy
import importlib
import pyparsing as pp

from xenon.base.datatypes import XenonObj, Sweepable
from xenon.base.exceptions import *
from xenon.base.expressions import Expression
from xenon.base.parsers import *

def recursiveSelect(root, objtype=object):
  """ Recursively selects all attributes of type objtype from root.  """
  if not isinstance(root, objtype):
    print type(root)
  assert(isinstance(root, objtype))
  selected_objs = []
  for obj in root.iterattrvalues(objtype=objtype):
    # Safety check to avoid infinite recursion.
    if obj == root:
      continue
    selected_objs.append(obj)
    selected_objs.extend(recursiveSelect(obj, objtype=objtype))
  return selected_objs

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
    self.tokens = list(parse_result.selection)

  def select(self, env):
    """ Return a list of objects in an environment selected by this selection.

    The environment is a dict-like object in that it must support the in and []
    operators, and it must return an object that does the same.
    """
    if not isinstance(env, XenonObj):
      raise TypeError("%s is not of type XenonObj." % str(env))

    # If there was no selection defined, then the selection is implicitly the
    # entire environment, recursively..
    if len(self.tokens) == 0:
      self.tokens.append(LIT_STARSTAR)

    current_view = env
    for i, token in enumerate(self.tokens):
      if token == LIT_STAR or token == LIT_STARSTAR:
        break
      try:
        current_view = getattr(current_view, token)
      except AttributeError:
        raise XenonSelectionError(".".join(self.tokens))
      if not isinstance(current_view, XenonObj):
        selection_path = ".".join(self.tokens[:i+1])
        raise TypeError("%s is not of type XenonObj.")

    selected_objs = []
    if token == LIT_STAR:
      selected_objs = [v for v in current_view.iterattrvalues(objtype=XenonObj)]
    elif token == LIT_STARSTAR:
      selected_objs = recursiveSelect(current_view, objtype=XenonObj)
    # Remember: * and ** return not just all the children of the current view,
    # but the current view itself.
    selected_objs.extend([current_view])
    return selected_objs

  def execute(self, env):
    return self.select(env)

class BeginCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ Begin command specifies sweep name and sweep type. """
    super(BeginCommand, self).__init__(lineno, line, parse_result)
    self.name = parse_result.sweep_name
    self.sweep_type = None  # TODO: Implement this later.

  def execute(self, sweep_obj):
    sweep_obj.initializeSweep(self.name, self.sweep_type)

class EndCommand(Command):
  def __init__(self, lineno, line, parse_result):
    """ End command contains no additional information. """
    super(EndCommand, self).__init__(lineno, line, parse_result)

  def execute(self, sweep_obj):
    sweep_obj.endSweep()

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
    else:
      self.value = parse_result.expression

  def setParam(self, sweep_obj):
    """ Set the parameter on all the selected objects to the provided value.

    The selected objects are taken from sweep_obj, the current sweep.

    The syntax purposely allows for * to select all members of an object, even
    ones that do not have this parameter. If, after going through all selected
    objects, none have the parameter as an attribute, issue a warning but do
    not abort.
    """
    value = None
    if isinstance(self.value, Expression):
      value = self.value.eval()
    else:
      value = self.value

    selected_objs = self.selection(sweep_obj)
    is_applied = False
    for obj in selected_objs:
      if hasattr(obj, self.param):
        setattr(obj, self.param, value)
        # Remove this parameter from obj.sweep_params_range, if it exists, so that
        # the sweep generator does not ignore this value.
        if isinstance(obj, Sweepable) and obj.hasSweepParamRange(self.param):
          obj.removeFromSweepParamRange(self.param)
        is_applied = True

    if not is_applied:
      raise XenonEmptySelectionError(self.param)

  def execute(self, sweep_obj):
    self.setParam(sweep_obj)

class UseCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(UseCommand, self).__init__(lineno, line, parse_result)
    self.package_path = list(parse_result.package_path)

  def execute(self, sweep_obj):
    package_path_str = ".".join(self.package_path)
    try:
      package = importlib.import_module(package_path_str)
      path_terminator = "*"  # For now, import everything into global namespace.
      # path_terminator = self.package_path[-1]
      if path_terminator == "*":
        # Import everything into the global namespace.
        for attr, val in package.__dict__.iteritems():
          if isinstance(val, XenonObj):
            sweep_obj.__dict__[attr] = copy.deepcopy(val)
      else:
        sweep_obj.__dict__[path_terminator] = package
    except ImportError as e:
      raise XenonImportError(self.package_path, e)

class GenerateCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(GenerateCommand, self).__init__(lineno, line, parse_result)
    self.target = parse_result.target

  def execute(self, sweep_obj):
    sweep_obj.addGenerateOutput(self.target)

class SweepCommand(Command):
  def __init__(self, lineno, line, parse_result):
    super(SweepCommand, self).__init__(lineno, line, parse_result)
    self.sweep_start = int(parse_result.range.start)
    self.sweep_end = int(parse_result.range.end)
    self.step = int(parse_result.range.step.amount)
    self.step_type = parse_result.range.step.type
    self.sweep_param = parse_result.sweep_param
    self.selection = SelectionCommand(lineno, line, parse_result)

  def execute(self, sweep_obj):
    selected_objs = self.selection(sweep_obj)
    is_applied_at_least_once = False
    for obj in selected_objs:
      if not isinstance(obj, Sweepable):
        continue
      ret = obj.setSweepParameter(self.sweep_param, self.sweep_start, self.sweep_end,
                                  self.step, self.step_type)
      if ret == SUCCESS:
        is_applied_at_least_once = True

    if not is_applied_at_least_once:
      raise XenonAttributeError(self.sweep_param)
