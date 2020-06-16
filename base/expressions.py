# eval_arith.py
#
# Copyright 2009, Paul McGuire
#
# Expansion on the pyparsing example simpleArith.py, to include evaluation
# of the parsed tokens.

import abc
import numpy as np
from pyparsing import Word, nums, alphas, alphanums, Combine, oneOf, \
    opAssoc, infixNotation, ParseException, delimitedList, MatchFirst
from xenon.base.datatypes import XenonObj
from xenon.base.common import getSelectedAttrOnView

class Expression(object):
  """ Base class for all evaluatable expressions. """
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def eval(self, env):
    pass

class EvalConstant(Expression):
    "Class to evaluate a parsed constant or variable"
    vars_ = {}
    def __init__(self, tokens):
        if len(tokens.constant):
            self.is_constant = True
            self.value = tokens.constant
        else:
            self.is_constant = False
            self.value = tokens.selection
    def eval(self, env):
        if self.is_constant:
            return float(self.value)
        # Otherwise, this is a selection.
        obj = getSelectedAttrOnView(self.value, env)
        if isinstance(obj, list):
            return np.array(obj)
        else:
            return float(obj)

class EvalSignOp(Expression):
    "Class to evaluate expressions with a leading + or - sign"
    def __init__(self, tokens):
        self.sign, self.value = tokens[0]
    def eval(self, env):
        mult = {'+':1, '-':-1}[self.sign]
        return mult * self.value.eval(env)

def operatorOperands(tokenlist):
    "generator to extract operators and operands in pairs"
    it = iter(tokenlist)
    while 1:
        try:
            yield (next(it), next(it))
        except StopIteration:
            break

class EvalMultOp(Expression):
    "Class to evaluate multiplication and division expressions"
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self, env):
        prod = self.value[0].eval(env)
        for op,val in operatorOperands(self.value[1:]):
            if op == '*':
                prod = prod * val.eval(env)
            elif op == '/':
                prod = prod / val.eval(env)
        return prod

class EvalAddOp(Expression):
    "Class to evaluate addition and subtraction expressions"
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self, env):
        sum_value = self.value[0].eval(env)
        for op,val in operatorOperands(self.value[1:]):
            if op == '+':
                sum_value = sum_value + val.eval(env)
            elif op == '-':
                sum_value = sum_value -  val.eval(env)
        return sum_value

class EvalComparisonOp(Expression):
    "Class to evaluate comparison expressions"
    opMap = {
        "<" : lambda a,b : a < b,
        "<=" : lambda a,b : a <= b,
        ">" : lambda a,b : a > b,
        ">=" : lambda a,b : a >= b,
        "!=" : lambda a,b : a != b,
        "==" : lambda a,b : a == b,
        }
    def __init__(self, tokens):
        self.value = tokens[0]
    def eval(self, env):
        val1 = self.value[0].eval(env)
        for op,val in operatorOperands(self.value[1:]):
            fn = EvalComparisonOp.opMap[op]
            val2 = val.eval(env)
            if not fn(val1,val2):
                break
            val1 = val2
        else:
            return True
        return False


# define the parser
integer = Word(nums).setResultsName("constant")
real = Combine(Word(nums) + "." + Word(nums)).setResultsName("constant")
constant = MatchFirst(real, integer).setResultsName("constant")
variable = Word(alphas, alphanums + "_").setResultsName("selection")
variable_chain = delimitedList(variable, delim=".").setResultsName("selection")
operand = real | integer | variable_chain | variable

signop = oneOf('+ -')
multop = oneOf('* /')
plusop = oneOf('+ -')

# use parse actions to attach EvalXXX constructors to sub-expressions
operand.setParseAction(EvalConstant)
arith_expr = infixNotation(operand,
    [
     (signop, 1, opAssoc.RIGHT, EvalSignOp),
     (multop, 2, opAssoc.LEFT, EvalMultOp),
     (plusop, 2, opAssoc.LEFT, EvalAddOp),
    ])

comparisonop = oneOf("< <= > >= != == <> LT GT LE GE EQ NE")
comp_expr = infixNotation(arith_expr,
    [
    (comparisonop, 2, opAssoc.LEFT, EvalComparisonOp),
    ])

def ParseExpression(text):
  try:
    return comp_expr.parseString(text, parseAll=True)[0]
  except ParseException as e:
    e.msg = "Failed to parse expression. " + e.msg
    raise e

def convertToExpressionTree(tokens=None):
  if not tokens:
    raise ParseException("Failed to parse expression")
  return ParseExpression(' '.join(tokens[0]))
