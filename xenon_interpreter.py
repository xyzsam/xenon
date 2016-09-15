#!/usr/bin/env python

import argparse
import pyparsing as pp
import sys

from xenon.base.commands import *
from xenon.base.command_bindings import getParser, getCommandClass
from xenon.base.datatypes import *
import xenon.base.xenon_exceptions as xe
from xenon.generators.xenon_generator import XenonGenerator

class XenonInterpreter():
  """ Executes a Xenon file.

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

  def handleXenonCommandError(self, command, err):
    msg = "On line %d: %s\n" % (command.lineno, command.line)
    msg += "%s: %s" % (err.__class__.__name__, str(err))
    print msg
    sys.exit(1)

  def handleXenonGeneratorError(self, target, err):
    msg = "Error occurred in generating %s\n" % target
    if isinstance(err, AttributeError):
      msg += "Do you have a generator for target %s?\n" % target
    msg += "%s: %s" % (err.__class__.__name__, str(err))
    print msg
    sys.exit(1)

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
      if DEBUG:
        print command.line
      try:
        command(current_sweep)
      except xe.XenonError as e:
        self.handleXenonCommandError(command, e)

    self.configured_sweep = current_sweep

  def generate_outputs(self):
    generator = XenonGenerator(self.configured_sweep)
    for output in self.configured_sweep.generate_outputs:
      try:
        handler = getattr(generator, "generate_%s" % output)
      except AttributeError as e:
        self.handleXenonGeneratorError(output, e)

      try:
        configs_generated = handler()
      except xe.XenonError as e:
        self.handleXenonGeneratorError(output, e)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("xenon_file", help="Xenon input file.")
  parser.add_argument("-d", "--debug", action="store_true", help="Turn on debugging output.")
  args = parser.parse_args()

  global DEBUG
  DEBUG = args.debug
  # TODO: These classes need some renaming.
  interpreter = XenonInterpreter(args.xenon_file)
  interpreter.parse()
  interpreter.execute()
  if DEBUG:
    interpreter.configured_sweep.dump()
  interpreter.generate_outputs()

if __name__ == "__main__":
  main()
