from commands import *
from parsers import *
from collections import namedtuple

Binding = namedtuple("Binding", "parserBuilder, commandClass")

BINDINGS_ = {
  CMD_BEGIN:    Binding(parserBuilder=buildBeginParser, commandClass=BeginCommand),
  CMD_END:      Binding(parserBuilder=buildEndParser, commandClass=EndCommand),
  CMD_SWEEP:    Binding(parserBuilder=buildSweepParser, commandClass=SweepCommand),
  CMD_SET:      Binding(parserBuilder=buildSetParser, commandClass=SetCommand),
  CMD_GENERATE: Binding(parserBuilder=buildGenerateParser, commandClass=GenerateCommand),
  CMD_USE:      Binding(parserBuilder=buildUseParser, commandClass=UseCommand),
  KW_FOR:       Binding(parserBuilder=buildSelectionParser, commandClass=SelectionCommand),
}

# Rather than building the parser every time it is required, build them once
# and return the built objects.
PARSER_BUILDER_OBJS_ = dict(
    (command, binding.parserBuilder()) for (command, binding) in BINDINGS_.iteritems())

def getParser(command):
  return PARSER_BUILDER_OBJS_[command]

def getCommandClass(command):
  """ Returns the class type for this command. """
  return BINDINGS_[command].commandClass
