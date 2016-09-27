from pyparsing import *
from xenon.base.expressions import convertToExpressionTree

CMD_BEGIN = "begin"
CMD_END = "end"
CMD_SWEEP = "sweep"
CMD_SET = "set"
CMD_REQUIRE = "require"
CMD_GENERATE = "generate"
CMD_USE = "use"

KW_FOR = "for"
KW_FROM = "from"
KW_TO = "to"
KW_ALL = "all"
KW_LINSTEP = "linstep"
KW_EXPSTEP = "expstep"

LIT_STAR = "*"

commands = [
    CMD_BEGIN,
    CMD_END,
    CMD_SWEEP,
    CMD_SET,
#    CMD_REQUIRE,
    CMD_GENERATE,
    CMD_USE,
]

other_keywords = [
    KW_FOR,
    KW_FROM,
    KW_TO,
    KW_ALL,
    KW_LINSTEP,
    KW_EXPSTEP,
]

special_literals = [
    LIT_STAR,
]

reserved = {}

SOL = LineStart()
EOL = LineEnd()
# An identifier must begin with a letter but can include numbers and underscores.
ident = Word(alphas, alphanums + "_")
string = QuotedString('"')
comment = Optional(pythonStyleComment).setResultsName("comment")
set_value = Word(alphanums, alphanums + "/")

def buildKeywords():
  global reserved
  for command in commands:
    reserved[command] = CaselessKeyword(command).setResultsName(command)
  for other in other_keywords:
    reserved[other] = CaselessKeyword(other).setResultsName(other)
  for literal in special_literals:
    reserved[literal] = Literal(literal)

buildKeywords()

def buildBeginParser():
  # Sweep names must begin with letters.
  sweepname = ident.setResultsName("sweep_name")
  sweepclass = ident.setResultsName("sweep_class")
  begin_statement = reserved[CMD_BEGIN] + sweepclass + sweepname + comment + EOL
  return begin_statement

def buildEndParser():
  """ The end command is defined by the following BNF:

  sweepname = ident
  end = "end" + sweepname
  """
  sweepname = ident.setResultsName("sweep_name")
  end_statement = reserved["end"] + sweepname + comment + EOL
  return end_statement

def buildGenerateParser():
  generate_parser = reserved["generate"] + ident.setResultsName("target")
  return generate_parser

def buildSelectionParser():
  """ A selection is an optional statement of the following form:

  selection = ["for" + ("*" | ((ident + ".") ...) ["*"])]
  """
  star_literals = reserved[LIT_STAR]
  selection_path = (
      Group(star_literals) |
      Group(delimitedList(ident, delim=".") + Optional(Literal(".").suppress() + star_literals))
      ).setResultsName("selection")
  selection = Optional(reserved["for"] + selection_path)
  return selection

def buildExpressionParser():
  """ An expression is a fallback for anything that does not match the above.

  It will be parsed to create a mathematical expression tree which will then be
  evaluated.
  """
  kws = MatchFirst(map(CaselessKeyword, [k for k in reserved.iterkeys()]))
  valid_expression = Group(OneOrMore(Word(alphanums + "()/+-<>=._")))
  return valid_expression.setResultsName("expression").setParseAction(convertToExpressionTree)

def buildSetParser():
  """ A set command is specified by the following BNF:

  variable = (alpha, alphanums | "_" | ".")
  string = "\" + (alphanums | "/") + "\""
  value = nums | expression
  set = "set" ident ["for" selection] value
  """
  selection = buildSelectionParser()
  constant = Word(nums).setResultsName("constant")
  stringValue = string.setResultsName("string")
  expression = buildExpressionParser().setResultsName("expression")
  set_parser = (
      reserved["set"] +
      ident.setResultsName("param") +
      selection +
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
  step_type = reserved["linstep"] | reserved["expstep"]
  step = Group(Optional(step_type, default="linstep").setResultsName("type") +
               Optional(Word(nums), default="1").setResultsName("amount")).setResultsName("step")
  range_parser = Group(
      reserved["from"] +
      Word(nums).setResultsName("start") +
      reserved["to"] +
      Word(nums).setResultsName("end") +
      step).setResultsName("range")
  return range_parser

def buildSweepParser():
  """ A sweep command is specified by the following BNF:

  sweep = "sweep" ident ["for" selection] (range | expression)

  TODO: Add ability to manually specify a list of sweep values.
  TODO: Add special syntax for boolean parameters.
  """
  selection = buildSelectionParser()
  sweep_range = buildRangeParser()
  sweep_parser = (
      reserved["sweep"] + ident.setResultsName("sweep_param") +
      selection + sweep_range)
  return sweep_parser

def buildUseParser():
  """ A use command is specified by the following BNF:

  package = ident
  use = "use" package[.package ...]

  The use command behaves in a similar way as the Python import keyword, with
  the following differences:
     - All use statements implicitly import everything (.*) inside the lowest
       specified package/module into the global namespace, so wildcards are not
       allowed.
     - Packages cannot be renamed with `as`.
  """
  package_path = Group(delimitedList(ident, delim=".")).setResultsName("package_path")
  use_parser = reserved["use"] + package_path
  return use_parser

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
