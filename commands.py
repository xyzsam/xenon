import abc
import pyparsing as pp
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

  def __init__(self, parse_result):
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
  def __init__(self, tokens):
    """ Constructs a selection argument given a set of parsed tokens. """
    # if not (isinstance(tokens, pp.ParseResults) or isinstance(tokens, str)):
    #   raise TypeError("tokens must be of type pyparsing.ParseResults or str!")
    self.tokens = tokens
    # This is an object reference to some object in some environment. It will
    # be resolved later.
    self.binding = None

  def bind(self, env):
    """ Bind this selection to an object in an environment.

    The environment is a dict-like object in that it must support the in and []
    operators, and it must return an object that does the same.
    """
    if self.tokens == "" or self.tokens == "*":
      # If there was no selection defined, then the selection is implicitly the
      # entire environment.
      return [env]

    current_view = None
    for token in tokens:
      if token == KW_STAR:
        self.binding = current_view if current_view != None else env
        return self.binding
      if token in env:
        current_view = env[token]

    # FIXME: Ensure that this returned object can be iterated over.
    self.binding = current_view
    return self.binding

  def execute(self, env):
    return self.bind(env)

class BeginCommand(Command):
  def __init__(self, parse_result):
    """ Begin command specifies sweep name and sweep type. """
    super(BeginCommand, self).__init__(parse_result)
    self.name = parse_result.sweep_name
    self.sweep_type = None  # TODO: Implement this later.

  def execute(self, sweep_obj):
    sweep_obj.initializeSweep(self.name, self.sweep_type)

class EndCommand(Command):
  def __init__(self, parse_result):
    """ End command contains no additional information. """
    super(EndCommand, self).__init__(parse_result)

  def execute(self, sweep_obj):
    sweep_obj.endSweep()

class SetCommand(Command):
  def __init__(self, parse_result):
    """ Construct a set command.

    A set command's value can be either a constant numeric value, a string, or
    an expression.
    """
    super(SetCommand, self).__init__(parse_result)
    self.param = parse_result.param
    self.selection = SelectionCommand(parse_result.selection)
    if len(parse_result.constant_value):
      self.value = float(parse_result.constant_value)
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

    selected_objects = self.selection(sweep_obj)
    is_applied_at_least_once = False
    for obj in selected_objects:
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

class SweepCommand(Command):
  def __init__(self, arg, sweep_range, selection=None):
    super(SweepCommand, self).__init__(parse_result)
    self.sweep_range = SweepRange(sweep_range)
    self.selection = SelectionCommand(selection)
