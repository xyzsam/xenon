# All keywords.
from pyparsing import Keyword, Literal

CMD_BEGIN = "begin"
CMD_END = "end"
CMD_SWEEP = "sweep"
CMD_SET = "set"
CMD_REQUIRE = "require"
CMD_GENERATE = "generate"
CMD_USE = "use"
CMD_SOURCE = "source"

KW_FOR = "for"
KW_FROM = "from"
KW_TO = "to"
KW_ALL = "all"
KW_LINSTEP = "linstep"
KW_EXPSTEP = "expstep"

KW_TRUE = "True"
KW_FALSE = "False"

LIT_STAR = "*"

commands = [
    CMD_BEGIN,
    CMD_END,
    CMD_SWEEP,
    CMD_SET,
    CMD_GENERATE,
    CMD_USE,
    CMD_SOURCE,
]

other_keywords = [
    KW_FOR,
    KW_FROM,
    KW_TO,
    KW_ALL,
    KW_LINSTEP,
    KW_EXPSTEP,
    KW_TRUE,
    KW_FALSE,
]

special_literals = [
    LIT_STAR,
]

reserved = {}

def buildKeywords():
  global reserved
  for command in commands:
    reserved[command] = Keyword(command).setResultsName(command)
  for other in other_keywords:
    reserved[other] = Keyword(other).setResultsName(other)
  for literal in special_literals:
    reserved[literal] = Literal(literal)

buildKeywords()
