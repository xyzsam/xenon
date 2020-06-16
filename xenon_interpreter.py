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
from xenon.base.parser import XenonParser
from xenon.base.datatypes import *

DEBUG = False

class XenonInterpreter():
  """ Executes a Xenon file.

  The result of the execution is a BaseDesignSweep object, which can then be passed
  to a ConfigGenerator object to expand the design sweep into each configuration.
  This result can be accessible through the XenonInterpreter.configured_sweep
  attribute.
  """
  def __init__(self, filename, test_mode=False):
    self.filename = filename
    # List of (line_number, ParseResult) tuples.
    self.commands_ = []
    # All the sweeps that have been configured, but not yet expanded.
    self.configured_sweeps = {}

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

  def parse(self):
    parser = XenonParser()
    self.commands_ = parser.parse(self.filename)

  def execute(self):
    current_sweep = None
    for command in self.commands_:
      print(command)
      try:
        current_sweep = command(current_sweep)
      except xe.XenonError as e:
        self.handleXenonCommandError(command, e)

      if current_sweep and current_sweep.isDone():
        current_sweep.validate()
        if current_sweep.name in self.configured_sweeps:
          raise xe.DuplicateSweepNameError(current_sweep.name)
        else:
          self.configured_sweeps[current_sweep.name] = current_sweep
        current_sweep = None

  def generate_outputs(self):
    all_generated_files = []
    for sweep in self.configured_sweeps.values():
      generated_files = sweep.generateAllOutputs()
      all_generated_files.extend(generated_files)
    return all_generated_files

  def run(self):
    self.parse()
    self.execute()
    genfiles = self.generate_outputs()
    return genfiles

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("xenon_file", help="Xenon input file.")
  parser.add_argument("-d", "--debug", action="store_true", help="Turn on debugging output.")
  args = parser.parse_args()

  global DEBUG
  DEBUG = args.debug
  interpreter = XenonInterpreter(args.xenon_file)
  interpreter.run()

if __name__ == "__main__":
  main()
