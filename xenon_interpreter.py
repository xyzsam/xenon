#!/usr/bin/env python

import argparse
import os
import pyparsing as pp
import sys
import types

# This is so that we can use the same fully qualified names in this script as
# in the rest of the code, which is designed so that py.test can correctly
# import modules.
sys.path.append(os.pardir)

import xenon.base.exceptions as xe
from xenon.base.commands import *
from xenon.base.command_bindings import getParser, getCommandClass
from xenon.base.datatypes import *
import xenon.generators

class XenonInterpreter():
  """ Executes a Xenon file.

  The result of the execution is a DesignSweep object, which can then be passed
  to a ConfigGenerator object to expand the design sweep into each configuration.
  This result can be accessible through the XenonInterpreter.configured_sweep
  attribute.
  """
  def __init__(self, filename):
    self.filename = filename
    # List of (line_number, ParseResult) tuples.
    self.commands_ = []
    # Parser object for the complete line.
    self.line_parser_ = buildCommandParser()

  def handleXenonCommandError(self, command, err):
    msg = "On line %d: %s\n" % (command.lineno, command.line)
    msg += "%s: %s\n" % (err.__class__.__name__, str(err))
    sys.stderr.write(msg)
    sys.exit(1)

  def handleGeneratorError(self, target, err):
    """ Handle certain exceptions thrown during generation.

    TODO: This isn't a great mechanism. Redo.
    """
    msg = "Error occurred in generating %s\n" % target
    if isinstance(err, ImportError):
      msg += "The generator module generator_%s was not found.\n" % target
    elif isinstance(err, AttributeError):
      msg += "Do you have a generator for target %s?\n" % target
    msg += "%s: %s\n" % (err.__class__.__name__, str(err))
    sys.stderr.write(msg)
    sys.exit(1)

  def handleSyntaxError(self, parser_err, line_number):
    spaces =  ' ' * (parser_err.col - 1)
    msg = "Invalid syntax on line %s:\n" % line_number
    msg += "  %s\n" % parser_err.line
    msg += "  %s^\n" % spaces
    msg += "  %s\n" % str(parser_err)
    sys.stderr.write(msg)
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

      if current_sweep.done:
        if DEBUG:
          interpreter.configured_sweep.dump()
        self.generate_outputs(current_sweep)
        current_sweep = DesignSweep()

  def generate_outputs(self, sweep):
    for output in sweep.generate_outputs:
      generator_module = self.get_generator_module(output)
      try:
        generator = generator_module.get_generator(sweep)
      except AttributeError as e:
        self.handleGeneratorError(output, e)

      try:
        configs_generated = generator.generate()
      except xe.XenonError as e:
        self.handleConfigGeneratorError(output, e)

  def get_generator_module(self, generate_target):
    """ Returns the module named generator_[generate_target].

    This module must be under xenon.generators. If such a module does not
    exist, then None is returned.
    """
    module_name = "generator_%s" % generate_target
    try:
      module = importlib.import_module(".".join(["xenon", "generators", module_name]))
    except ImportError as e:
      self.handleGeneratorError(generate_target, e)
    return module

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("xenon_file", help="Xenon input file.")
  parser.add_argument("-d", "--debug", action="store_true", help="Turn on debugging output.")
  args = parser.parse_args()

  global DEBUG
  DEBUG = args.debug
  interpreter = XenonInterpreter(args.xenon_file)
  interpreter.parse()
  interpreter.execute()

if __name__ == "__main__":
  main()
