import pyparsing as pp

from parser_builders import *
from commands import *
from datatypes import SweepConfigFileParser, DesignSweep

def tryTest(parser, text):
  """ Returns whether the text was successfully parsed by parser or not. """
  try:
    result = parser.parseString(text, parseAll=True)
    return result
  except pp.ParseException as x:
    return None

def tryAllTestCases(name, parser, testcases):
  print "Testing %s" % name
  print "===================="

  success = True
  for testcase in testcases:
    result = tryTest(parser, testcase[0])
    parse_success = (result != None)
    is_expected = parse_success == testcase[1]
    success &= is_expected
    if not is_expected:
      print "Failed testcase \"%s\": got %s, expected %s" % (testcase[0], result, testcase[1])

  if success:
    print "All tests passed!"
  print ""

def testBeginParser():
  begin_parser = buildBeginParser()
  testcases = [("begin sweep mysweep", True),
               ("BEGIN SWEEP MySweep  ", True),
               ("  BeGIn sWeEp sweep123", True),
               ("begin sweep sweep_nothing_2  ", True),
               ("begin sweep sweep_nothing_2 extra", False),
               ("begin sweep 123sweep", False),
               ("begin sweep sweep.$#", False),
               ("begin sweep2", False),
               ("begin sweep", False),
               ("sweep mysweep2", False),
               ]
  tryAllTestCases("begin", begin_parser, testcases)

def testEndParser():
  end_parser = buildEndParser()
  testcases = [("end sweep", True),
               ("END SWEEP", True),
               ("END", False),
               ("sweep", False),
               ("END SWEEP mysweep", False)
               ]
  tryAllTestCases("end", end_parser, testcases)

def testGenerateParser():
  generate_parser = buildGenerateParser()
  testcases = [("generate configs", True),
               ("generate trace", True),
               ("generate condor", True),
               ("generate anything", True),
               ("not a generate", False),
               ("generate", False),
               ]
  tryAllTestCases("generate", generate_parser, testcases)

def testCommandParser():
  """ Tests whether a line begins with a valid command. """
  command_parser = buildCommandParser()
  testcases = [("begin sweep mysweep", True),
               ("end sweep", True),
               ("end", True),
               ("invalid command", False),
               ("require something something something", True),
               ("# This is a comment.", True),
               ("generate trace", True),
               ("generate trace # And a comment", True),
               ("output something", False),
               ("require expression", True),
               ("sweep something", True),
               ("condor this and that", False),
              ]
  tryAllTestCases("commands", command_parser, testcases)

def testSetParser():
  set_parser = buildSetParser()
  testcases = [("set param value", True),
               ("set param for benchmark value", True),
               ("set param for benchmark.* value", True),
               ("set param for benchmark.func value", True),
               ("set param for benchmark.func.* value", True),
               ("set param for benchmark.func.* 42", True),
               ("set param for benchmark.array something", True),
               ("set param_factor for * (expression)", True),
               ("set param_factor for * (my.expression)", True),
               ("set param_factor for * (expression)/that + something", True),
               ("set param_factor for something.*   (expression)/that + does - something", True),
               ("set param for benchmark.func.* 42value", False),
               ("set param for benchmark.func.* 42.value", False),
               ("set param for benchmark.func.* value.", False),
               ("set param", False),
               ("set", False),
               ]
  tryAllTestCases("set", set_parser, testcases)

def testSelectionParser():
  selection_parser = buildSelectionParser()
  testcases = [("for funcName", True),
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
  tryAllTestCases("selection", selection_parser, testcases)

def testRangeParser():
  range_parser = buildRangeParser()
  testcases = [("from 1 to 8 linstep 2", True),
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
  tryAllTestCases("range", range_parser, testcases)

def testSweepParser():
  sweep_parser = buildSweepParser()
  testcases = [("sweep param from 1 to 8", True),
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
  tryAllTestCases("sweep", sweep_parser, testcases)

def getInitializedSweep(sweep_name):
  """ Return an initialized sweep. Consider putting this in DesignSweep. """
  sweep = DesignSweep()
  begin_parser = buildBeginParser()
  results = begin_parser.parseString("begin sweep %s" % sweep_name, parseAll=True)
  begin_command = BeginCommand(results)
  begin_command(sweep)
  return sweep

def closeSweep(sweep):
  end_parser = buildEndParser()
  results = end_parser("end sweep")
  end_command = EndCommand(results)
  end_command(sweep)

def testBeginAndEndCommands():
  sweep = getInitializedSweep("mysweep")
  assert(sweep.name == "mysweep")
  assert(sweep.sweep_type == None)

  closeSweep(sweep)
  assert(sweep.done == True)

def testSimpleSetCommands():
  """ Simple == no selections or expressions. """
  sweep = getInitializedSweep("mysweep")
  set_parser = buildSetParser()
  results = set_parser.parseString("set output_dir \"path\"")
  set_command = SetCommand(results)
  set_command(sweep)
  assert(sweep.output_dir == "path")

  results = set_parser.parseString("set output_dir \"path/to/output\"")
  set_command = SetCommand(results)
  set_command(sweep)
  assert(sweep.output_dir == "path/to/output")

def runCommandTests():
  testBeginAndEndCommands()
  testSimpleSetCommands()

  print "All tests passed!"


def runParsingTests():
  testBeginParser()
  testEndParser()
  testGenerateParser()
  testSetParser()
  testSelectionParser()
  testRangeParser()
  testSweepParser()
  testCommandParser()

def testParseFile(filename):
  parser = SweepConfigFileParser(filename)
  parser.parse()

def main():
  buildKeywords()
  # runParsingTests()
  runCommandTests()
  # testParseFile("example.sweep")

if __name__ == "__main__":
  main()
