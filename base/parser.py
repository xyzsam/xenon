from collections import namedtuple
import os
import sys

from xenon.base.commands import *
from xenon.base.parser_builders import *

Binding = namedtuple("Binding", "parserBuilder, commandClass")

BINDINGS_ = {
  CMD_BEGIN:    Binding(parserBuilder=buildBeginParser, commandClass=BeginCommand),
  CMD_END:      Binding(parserBuilder=buildEndParser, commandClass=EndCommand),
  CMD_SWEEP:    Binding(parserBuilder=buildSweepParser, commandClass=SweepCommand),
  CMD_SET:      Binding(parserBuilder=buildSetParser, commandClass=SetCommand),
  CMD_GENERATE: Binding(parserBuilder=buildGenerateParser, commandClass=GenerateCommand),
  CMD_USE:      Binding(parserBuilder=buildUseParser, commandClass=UseCommand),
  CMD_SOURCE:   Binding(parserBuilder=buildSourceParser, commandClass=SourceCommand),
  KW_FOR:       Binding(parserBuilder=buildSelectionParser, commandClass=SelectionCommand),
}

# Rather than building the parser every time it is required, build them once
# and return the built objects.
PARSER_BUILDER_OBJS_ = dict((command, binding.parserBuilder())
                            for (command, binding) in BINDINGS_.items())

def getParser(command):
  return PARSER_BUILDER_OBJS_[command]

def getCommandClass(command):
  """ Returns the class type for this command. """
  return BINDINGS_[command].commandClass

class XenonParser():
  def __init__(self):
    pass

  def parse(self, filename, current_dir=""):
    line_parser = buildCommandParser()
    commands = []
    if not os.path.isabs(filename):
      filename = os.path.join(current_dir, filename)
    with open(filename) as f:
      for line_number, line in enumerate(f):
        line_number += 1  # Line numbers aren't zero indexed.
        line = line.strip()
        if not line:
          continue
        # Determine if this line begins with a valid command or not.
        result = None
        try:
          result = line_parser.parseString(line, parseAll=True)
          if result.command == "":
            continue
        except pp.ParseException as x:
          self.handleSyntaxError(x, line_number)

        # If so, parse the rest of the line.
        line_command = result.command
        try:
          # Reform the line without the comments.
          line = result.command + ' ' + ' '.join(result.rest[0])
          result = getParser(result.command).parseString(line, parseAll=True)
        except pp.ParseException as x:
          self.handleSyntaxError(x, line_number)

        command = getCommandClass(line_command)(line_number, line, result)

        if isinstance(command, SourceCommand):
          parser = XenonParser()
          sourced_commands = parser.parse(
              command.source_file,
              current_dir=os.path.dirname(os.path.realpath(filename)))
          commands.extend(sourced_commands)
        else:
          commands.append(command)
    return commands

  def handleSyntaxError(self, parser_err, line_number):
    spaces =  ' ' * (parser_err.col - 1)
    msg = "Invalid syntax on line %s:\n" % line_number
    msg += "  %s\n" % parser_err.line
    msg += "  %s^\n" % spaces
    msg += "  %s\n" % str(parser_err)
    sys.stderr.write(msg)
    sys.exit(1)
