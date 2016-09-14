import argparse
import pyparsing as pp
import sys

from base_datatypes import *
from commands import *
from command_bindings import getParser, getCommandClass
import xenon_exceptions as xe

class XenonInterpreter(object):
  """ Executes a Xenon a file.

  The result of the execution is a DesignSweep object, which can then be passed
  to a XenonGenerator object to expand the design sweep into each configuration.
  This result can be accessible through the XenonInterpreter.configured_sweep
  attribute.
  """
  def __init__(self, filename):
    self.filename = filename
    # List of (line_number, ParseResult) tuples.
    self.commands_ = []
    # Parser object for the complete line.
    self.line_parser_ = buildCommandParser()
    # The result of the execution.
    self.configured_sweep = None

  def handleXenonError(self, command, e):
    msg = "On line %d: %s\n" % (command.lineno, command.line)
    msg += "%s: %s" % (e.__class__.__name__, str(e))

  def handleSyntaxError(self, parser_err, line_number):
    spaces =  ' ' * (parser_err.col - 1)
    msg = "Invalid syntax on line %s:\n" % line_number
    msg += "  %s\n" % parser_err.line
    msg += "  %s^\n" % spaces
    msg += "  %s" % str(parser_err)
    print msg
    sys.exit(1)

  def parse(self):
    with open(self.filename) as f:
      for line_number, line in enumerate(f):
        line_number += 1  # Line numbers aren't zero indexed.
        line = line.strip()
        if not line:
          continue
        # Determine if this line begins with a valid command or not.
        result = None
        try:
          result = self.line_parser_.parseString(line, parseAll=True)
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

        commandClass = getCommandClass(line_command)(line_number, line, result)
        self.commands_.append(commandClass)

  def execute(self):
    current_sweep = DesignSweep()
    for command in self.commands_:
      print command.line
      try:
        command(current_sweep)
      except xe.XenonError as e:
        self.handleXenonError(command, e)

    self.configured_sweep = current_sweep

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("xenon_file", help="Xenon input file.")
  args = parser.parse_args()

  interpreter = XenonInterpreter(args.xenon_file)
  interpreter.parse()
  interpreter.execute()
  interpreter.configured_sweep.dump()

if __name__ == "__main__":
  main()
