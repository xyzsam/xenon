import pyparsing as pp
import sys

from datatypes import *
from commands import *
from command_bindings import getParser, getCommandClass
import xenon_exceptions as xe

class XenonFileParser(object):
  """ The parsed contents of a sweep file.  """

  def __init__(self, filename=None):
    # (string) Filename.
    self.filename = filename
    # List of (line_number, ParseResult) tuples.
    self.commands = []
    # Parser object for the complete line.
    self.line_parser_ = buildCommandParser()

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
        line = line.lower()
        line = line.strip()
        if not line:
          continue
        # Determine if this line begins with a valid command or not.
        result = None
        try:
          result = self.line_parser_.parseString(line, parseAll=True)
          if result.comment:
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
        self.commands.append(commandClass)
