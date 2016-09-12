from pyparsing import *
from expressions import convertToExpressionTree

CMD_BEGIN = "begin"
CMD_END = "end"
CMD_SWEEP = "sweep"
CMD_SET = "set"
CMD_REQUIRE = "require"
CMD_GENERATE = "generate"

KW_FOR = "for"
KW_FROM = "from"
KW_TO = "to"
KW_ALL = "all"
KW_STAR = "*"
KW_LINSTEP = "linstep"
KW_EXPSTEP = "expstep"

commands = [
    CMD_BEGIN,
    CMD_END,
    CMD_SWEEP,
    CMD_SET,
#    CMD_REQUIRE,
    CMD_GENERATE,
]

other_keywords = [
    KW_FOR,
    KW_FROM,
    KW_TO,
    KW_ALL,
    KW_STAR,
    KW_LINSTEP,
    KW_EXPSTEP,
]

# attributes = [
#     "output_dir",
#     "source_dir",
#     "simulator",
#     "memory_type",
#     "sweep_type",
#     "output",
#     "trace",
#     "condor",
# ]

keywords = {}

SOL = LineStart()
EOL = LineEnd()
# An identifier must begin with a letter but can include numbers and underscores.
ident = Word(alphas, alphanums + "_")
string = QuotedString('"')
comment = Optional(pythonStyleComment).setResultsName("comment")
set_value = Word(alphanums, alphanums + "/")

def buildKeywords():
  global keywords
  for command in commands:
    keywords[command] = CaselessKeyword(command).setResultsName("command")
  for other in other_keywords:
    keywords[other] = CaselessKeyword(other).setResultsName(other)

def buildBeginParser():
  # Sweep names must begin with letters.
  sweepname = ident.setResultsName("sweep_name")
  begin_statement = keywords["begin"] + keywords["sweep"] + sweepname + comment + EOL
  return begin_statement

def buildEndParser():
  end_statement = keywords["end"] + keywords["sweep"] + comment + EOL
  return end_statement

def buildGenerateParser():
  generate_parser = keywords["generate"] + ident.setResultsName("target")
  return generate_parser

def buildSelectionParser():
  """ A selection is a statement of the following form:

  selection = "for" + ("*" | ((ident + ".") ...) ["*"])
  """
  selection = Group(keywords["for"] + (
      Literal("*") | Group(delimitedList(ident, delim=".") + Optional(Literal (".*"))))
      ).setResultsName("selection")
  return selection

def buildExpressionParser():
  """ An expression is a fallback for anything that does not match the above.

  It will be parsed to create a mathematical expression tree which will then be
  evaluated.
  """
  kws = MatchFirst(map(CaselessKeyword, [k for k in keywords.iterkeys()]))
  valid_expression = Group(OneOrMore(Word(alphanums + "()/+-<>=._")))
  # return ~kws + valid_expression.setResultsName("expression") #.setParseAction(convertToExpressionTree)
  return valid_expression.setResultsName("expression").setParseAction(convertToExpressionTree)

def buildSetParser():
  """ A set command is specified by the following BNF:

  variable = (alpha, alphanums | "_" | ".")
  string = "\" + (alphanums | "/") + "\""
  value = nums | expression
  set = "set" ident ["for" selection] value
  """
  selection = buildSelectionParser()
  constant = Word(nums + ".").setResultsName("constant")
  stringValue = string.setResultsName("string") 
  expression = buildExpressionParser().setResultsName("expression")
  set_parser = (
      keywords["set"] +
      ident.setResultsName("param") +
      Optional(selection) +
      (constant | stringValue | expression)
  )
  return set_parser

def buildRangeParser():
  """ A range is specified by the following BNF:

  start = nums
  end = nums
  amount = nums
  step = "linstep" | "expstep"
  range = "from" start "to" end [step amount]
  """
  step_type = keywords["linstep"] | keywords["expstep"]
  step = Group(step_type.setResultsName("step_type") +
               Word(nums).setResultsName("step_amount"))
  range_parser = Group(
      keywords["from"] +
      Word(nums).setResultsName("start") +
      keywords["to"] +
      Word(nums).setResultsName("end") +
      Optional(step, default=["linstep", "1"]))
  return range_parser

def buildSweepParser():
  """ A sweep command is specified by the following BNF:

  sweep = "sweep" ident ["for" selection] (range | expression)

  TODO: Add ability to manually specify a list of sweep values.
  TODO: Add special syntax for boolean parameters.
  """
  selection = buildSelectionParser()
  sweep_range = buildRangeParser()
  sweep_parser = keywords["sweep"] + ident.setResultsName("sweep_param") + Optional(selection) + sweep_range
  return sweep_parser

def buildCommandParser():
  """ Parses a complete command line.

  This will match if the first word is a recognized keyword, or the line is a comment.
  Based on the matched keyword, the appropriate parser object should be invoked
  to parse the rest of the line.
  """
  command_keywords = []
  line_with_command = (
      SOL +
      MatchFirst(map(CaselessKeyword, commands)).setResultsName("command") +
      Optional(Group(OneOrMore(Word(printables, excludeChars='#')))).setResultsName("rest") +
      comment
      )
  comment_line = SOL + comment + EOL
  command = MatchFirst([comment_line, line_with_command])
  return command
