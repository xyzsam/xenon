# Unit tests for grammar parsing.
#
# These tests only check if parsing did or did not throw an exception, NOT
# whether the parser bound the right results to the right attributes.

import pyparsing as pp
import unittest

from xenon.base.commands import *
from xenon.base.designsweeptypes import ExhaustiveSweep
from xenon.base.parser_builders import *

# Put the base unittest class in a separate class so that it doesn't get run as
# a test case.
class Common(object):
  class ParserTestCase(unittest.TestCase):
    def parse(self, text):
      self.parser.parseString(text, parseAll=True)

    def tryTest(self, text, expected_success):
      if expected_success:
        self.parse(text)
      else:
        self.assertRaises(pp.ParseException, self.parse, text)

    def test_all(self):
      for text, expected_success in self.testcases:
        self.tryTest(text, expected_success)

class BeginParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildBeginParser()
    self.testcases = [("begin DesignSweep mysweep", True),
                      ("begin CustomSweep sweep_nothing_2  ", True),
                      ("begin sweep sweepname", True),
                      ("begin Sweep sweep_nothing_2 extra", False),
                      ("BEGIN ExhaustiveSweep MySweep  ", False),
                      ("  BeGIn ExhaustiveSweep sweep123", False),
                      ("begin sweep 123sweep", False),
                      ("begin sweep sweep.$#", False),
                      ("begin sweep2", False),
                      ("begin sweep", False),
                      ("sweep mysweep2", False),
                      ]

class EndParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildEndParser()
    self.testcases = [("end sweep", True),
                      ("END SWEEP", False),
                      ("END", False),
                      ("sweep", False),
                      ("END SWEEP mysweep", False)
                      ]

class GenerateParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildGenerateParser()
    self.testcases = [("generate configs", True),
                      ("generate trace", True),
                      ("generate condor", True),
                      ("generate anything", True),
                      ("not a generate", False),
                      ("generate", False),
                      ]

class CommandParser(Common.ParserTestCase):
  """ Tests whether a line begins with a valid command. """
  def setUp(self):
    self.parser = buildCommandParser()
    self.testcases = [("begin sweep mysweep", True),
                      ("end sweep", True),
                      ("end", True),
                      ("invalid command", False),
                      ("# This is a comment.", True),
                      ("generate trace", True),
                      ("generate trace # And a comment", True),
                      ("output something", False),
                      ("sweep something", True),
                      ("condor this and that", False),
                     ]

  @unittest.skip("Require commands not yet supported.")
  def test_require_commands(self):
    self.testcases = [("require something something something", True),
                      ("require (expression)", True),
                      ]
    self.test_all(self)

class SetParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildSetParser()
    self.testcases = [
        ("set param value", True),
        ("set param for benchmark value", True),
        ("set param for benchmark.* value", True),
        ("set param for benchmark.func value", True),
        ("set param for benchmark.func.* value", True),
        ("set param for benchmark.func.* 42", True),
        ("set param for benchmark.array something", True),
        ("set param for benchmark [1,2,3]", True),
        ("set param for benchmark [1, 2, 3 ]", True),
        ("set param for benchmark [1,2,True]", True),
        ("set param for benchmark [False,True]", True),
        ("set param for benchmark [\"a\", \"b\", \"c\"]", True),
        ("set param for benchmark [\"a\", 0, \"c\"]", True),
        ("set param for benchmark ['a', 0, 'c']", True),
        ("set param_factor for * (expression)", True),
        ("set param_factor for * (my.expression)", True),
        ("set param_factor for * (expression)/that + something", True),
        ("set param_factor for something.*   (expression)/that + does - something", True),
        ("set param for benchmark.func.* 42value", False),
        ("set param for benchmark.func.* 42.value", False),
        ("set param for benchmark.func.* value.", False),
        ("set param for benchmark [a, b, c]", False),
        ("set param for benchmark [a, 0, 2]", False),
        ("set param", False),
        ("set", False),
        ]

class SelectionParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildSelectionParser()
    self.testcases = [("for funcName", True),
                      ("for function_name", True),
                      ("for benchmark_name", True),
                      ("for benchmark_name.something", True),
                      ("for benchmark_name.*", True),
                      ("for benchmark_name.func_name_123", True),
                      ("for benchmark_name.func_name_123.array3", True),
                      ("for benchmark_name.func_name_123.*", True),
                      ("for *", True),
                      ("for *.*", False),
                      ("for *.*.*", False),
                      ("for *.something", False),
                      ("for *Bad.*.*", False),
                      ("for ", False),
                      ("for benchmark/", False),
                      ("for benchmark-name/", False),
                      ("for 123-benchmark.*", False),
                      ("for benchmark.func/", False),
                      ("for benchmark.%*", False),
                      ("for benchmark.#$", False),
                      ("for benchmark.#$.label", False),
                      ("for benchmark.#$.*", False),
                      ]

class RangeParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildRangeParser()
    self.testcases = [("from 1 to 8 linstep 2", True),
                      ("from 1 to 8 expstep 2", True),
                      ("from 1 to 8", True),
                      ("", False),
                      ("from 1 to 8 step 2", False),
                      ("from x to y linstep z", False),
                      ("from 1 to 8 linstep x", False),
                      ("from 1", False),
                      ("to 2", False),
                      ("step 1", False),
                      ]

class SweepParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildSweepParser()
    self.testcases = [("sweep param from 1 to 8", True),
                      ("sweep param from 1 to 8 linstep 2", True),
                      ("sweep param from 20 to 32 expstep 2", True),
                      ("sweep param from 20 to 32 expstep 2", True),
                      ("sweep param for benchmark.array from 1 to 8", True),
                      ("sweep param for benchmark.array from 2 to 16 linstep 2", True),
                      ("sweep param for benchmark.func from 1 to 8", True),
                      ("sweep param_factor for * from 1 to 8 linstep 4", True),
                      ("sweep param for benchmark.func.loop from 1 to 8 expstep 3", True),
                      ("sweep param_factor for *.something", False),
                      ("sweep param", False),
                      ("sweep param from 1", False),
                      ("sweep param for 1", False),
                      ]

class UseParser(Common.ParserTestCase):
  def setUp(self):
    self.parser = buildUseParser()
    self.testcases = [("use package", True),
                      ("use package_name.module", True),
                      ("use package.subpackage.module", True),
                      ("use package.*", True),
                      ("use package.something.*", True),
                      ("use", False),
                      ("use *", False),
                      ("use .*", False),
                      ("use *.*", False),
                      ]

class CommentParser(Common.ParserTestCase):
  """ This test ensures we can distinguish comments and commands. """
  def setUp(self):
    self.parser = buildCommandParser()
    self.testcases = []

  def test_inline_comments(self):
    results = self.parser.parseString("set param 3   #   This is a comment.", parseAll=True)
    self.assertEqual(str(results.command), "set")
    self.assertEqual(' '.join(results.rest[0]), "param 3")
    self.assertEqual(results.comment, "#   This is a comment.")

    results = self.parser.parseString("use package.module # comment.", parseAll=True)
    self.assertEqual(str(results.command), "use")
    self.assertEqual(' '.join(results.rest[0]), "package.module")
    self.assertEqual(results.comment, "# comment.")

  def test_whole_line_comment(self):
    results = self.parser.parseString("# This is a comment only.", parseAll=True)
    self.assertEqual(str(results.command), "")
    self.assertEqual(len(results.rest), 0)
    self.assertEqual(str(results.comment), "# This is a comment only.")

if __name__ == "__main__":
  unittest.main()
