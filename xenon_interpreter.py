import argparse
import sys

from base_datatypes import DesignSweep
from xenon_file_parser import XenonFileParser
import xenon_exceptions as xe

class XenonInterpreter(object):
  def __init__(self, filename):
    self.filename = filename
    self.fileparser = None

  def handleXenonError(self, command, e):
    msg = "On line %d: %s\n" % (command.lineno, command.line)
    msg += "%s: %s" % (e.__class__.__name__, str(e))
    print msg
    sys.exit(1)

  def execute(self):
    self.fileparser = XenonFileParser(self.filename)
    self.fileparser.parse()

    current_sweep = DesignSweep()
    for command in self.fileparser.commands:
      try:
        command(current_sweep)
      except xe.XenonError as e:
        self.handleXenonError(command, e)

    return current_sweep

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("xenon_file", help="Xenon input file.")
  args = parser.parse_args()

  interpreter = XenonInterpreter(args.xenon_file)
  sweep = interpreter.execute()
  sweep.dump()

if __name__ == "__main__":
  main()
