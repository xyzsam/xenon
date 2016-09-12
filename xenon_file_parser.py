import pyparsing as pp
import sys

from datatypes import *
from commands import *

class XenonFileParser(object):
  """ The parsed contents of a sweep file.  """

  def __init__(self, filename=None):
    # (string) Filename.
    self.filename = filename
    # List of (line_number, ParseResult) tuples.
    self.commands_ = []
    # Dict of commands to their parser objects.
    self.command_parsers_ = {}
    # Parser object for the complete line.
    self.line_parser_ = buildCommandParser()

    self.buildCommandParsers_()

  def buildCommandParsers_(self):
    self.command_parsers_[CMD_BEGIN] = buildBeginParser()
    self.command_parsers_[CMD_END] = buildEndParser()
    self.command_parsers_[CMD_SWEEP] = buildSweepParser()
    self.command_parsers_[CMD_SET] = buildSetParser()
    # self.command_parsers_[CMD_REQUIRE] = buildRequireParser()
    self.command_parsers_[CMD_GENERATE] = buildGenerateParser()

  def buildActionTable_(self):
    self.action_table_[CMD_BEGIN] = "initializeSweep"
    self.action_table_[CMD_END] = "endSweep"

  def printException_(self, err, line, line_number, msg=""):
    """ Prints exception with pointer to error column. """
    spaces =  ' ' * (err.col - 1)
    print ""
    print "Error on line %d: %s" % (line_number, msg)
    print "  ", line
    print "   %s^" % spaces
    print str(err)
    print ""

  def createCommand(self, parse_result):
    if parse_result.command == CMD_BEGIN:
      return BeginCommand(parse_result)
    elif parse_result.command == CMD_END:
      return EndCommand(parse_result)
    elif parse_result.command == CMD_SET:
      return SetCommand(parse_result)
    elif parse_result.command == CMD_GENERATE:
      return GenerateCommand(parse_result)
    elif parse_result.command == CMD_SWEEP:
      return SweepCommand(parse_result)
    return None

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
          self.printException_(x, line, line_number, "Unknown command")
          sys.exit(1)

        # If so, parse the rest of the line.
        try:
          # Reform the line without the comments.
          line = result.command + ' ' + ' '.join(result.rest[0])
          result = self.command_parsers_[result.command].parseString(line, parseAll=True)
          # print result.constant, result.expression
          print type(result.expression)
        except pp.ParseException as x:
          self.printException_(x, line, line_number)
          sys.exit(1)

        # Add this to commands_.
        # command = self.createCommand(result)
        self.commands_.append((line_number, result))

  def execute(self):
    current_sweep = DesignSweep()
    for line_num, command in self.commands_:
      action_func = getattr(current_sweep, self.action_table_[command.command])
      action_func(command)


