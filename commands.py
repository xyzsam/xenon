import abc
import importlib
import pyparsing as pp

import xenon_exceptions as xe
from parsers import *
from expressions import Expression

class Command(object):
  """ Commands describe an action to perform on a sweep.

  Subclasses must implement the execute method, which can take an arbitrary
  number of arguments. Generally, all that is required is a DesignSweep object, as
  it (should) encapsulates all the state needed.

  Commands can be invoked using operator() like command(sweep_obj), for
  brevity. This is equivalent to calling execute().
  """
  __metaclass__ = abc.ABCMeta

  def __init__(self, line, parse_result):
    # Line number in the Xenon file.
    self.line = line
    # Keep a copy of the original parsed result around.
    self.parse_result = parse_result

  @abc.abstractmethod
  def execute(self, *args):
    pass

  def __call__(self, *args):
    return self.execute(*args)

  def __str__(self):
    return str(parse_result)

class SelectionCommand(Command):
  def __init__(self, line, parse_result):
    """ Constructs a selection argument given a set of parsed tokens. """
    super(SelectionCommand, self).__init__(line, parse_result.selection)
    self.tokens = list(parse_result.selection)
    # This is an object reference to some object in some environment. It will
    # be resolved later.
    self.selected_objs = None

  def get_non_special_attr_values(self, obj):
    return [getattr(obj, attr) for attr in dir(obj)
            if not attr.startswith("__") and not callable(getattr(obj, attr))]

  def select(self, env):
    """ Return a list of objects in an environment selected by this selection.

    The environment is a dict-like object in that it must support the in and []
    operators, and it must return an object that does the same.
    """
    if len(self.tokens) == 0:
      # If there was no selection defined, then the selection is implicitly the
      # entire environment.
      return [env]

    if self.tokens[0] == KW_STAR:
      # If the selection was "*", then return all first level objects under the
      # environment.
      return self.get_non_special_attr_values(env)

    current_view = env
    for token in self.tokens:
      if token == KW_STAR:
        break
      try:
        current_view = getattr(current_view, token)
      except AttributeError:
        raise xe.XenonSelectionError(".".join(self.tokens))

    if token == KW_STAR:
      self.selected_objs = self.get_non_special_attr_values(current_view)
    else:
      self.selected_objs = [current_view]
    return self.selected_objs

  def execute(self, env):
    return self.select(env)

class BeginCommand(Command):
  def __init__(self, line, parse_result):
    """ Begin command specifies sweep name and sweep type. """
    super(BeginCommand, self).__init__(line, parse_result)
    self.name = parse_result.sweep_name
    self.sweep_type = None  # TODO: Implement this later.

  def execute(self, sweep_obj):
    sweep_obj.initializeSweep(self.name, self.sweep_type)

class EndCommand(Command):
  def __init__(self, line, parse_result):
    """ End command contains no additional information. """
    super(EndCommand, self).__init__(line, parse_result)

  def execute(self, sweep_obj):
    sweep_obj.endSweep()

class SetCommand(Command):
  def __init__(self, line, parse_result):
    """ Construct a set command.

    A set command's value can be either a constant numeric value, a string, or
    an expression.
    """
    super(SetCommand, self).__init__(line, parse_result)
    self.param = parse_result.param
    self.selection = SelectionCommand(line, parse_result)
    if len(parse_result.constant):
      self.value = float(parse_result.constant)
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
    is_applied_at_least_once = False
    for obj in selected_objs:
      try:
        obj.__setattr__(self.param, value)
        is_applied_at_least_once = True
      except AttributeError as e:
        continue

    if not is_applied_at_least_once:
      print ("Warning: did not find any objects in the provided sweep for which "
             "the parameter {0} could be set to {1}".format(self.param, self.value))

  def execute(self, sweep_obj):
    self.setParam(sweep_obj)

class UseCommand(Command):
  def __init__(self, line, parse_result):
    super(UseCommand, self).__init__(line, parse_result)
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
          # Don't import builtins or metadata about the package (name, file, etc.).
          if not attr.startswith("__"):
            sweep_obj.__dict__[attr] = val
      else:
        sweep_obj.__dict__[path_terminator] = package
    except ImportError as e:
      raise xe.XenonImportError(self.package_path)

class GenerateCommand(Command):
  def __init__(self, line, parse_result):
    super(GenerateCommand, self).__init__(line, parse_result)

class SweepCommand(Command):
  def __init__(self, line, arg, sweep_range, selection=None):
    super(SweepCommand, self).__init__(line, parse_result)
    self.sweep_range = SweepRange(sweep_range)
    self.selection = SelectionCommand(line, selection)
