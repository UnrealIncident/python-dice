"""
Dice notation grammar

PyParsing is patched to make it easier to work with, by removing features
that get in the way of development and debugging. See the dice.utilities
module for more information.
"""

from __future__ import absolute_import, unicode_literals, division
from __future__ import print_function

from pyparsing import (CaselessLiteral, Forward, Group, Keyword, Literal,
    OneOrMore, Optional, ParserElement, StringStart, StringEnd, Suppress,
    Word, ZeroOrMore, delimitedList, nums, opAssoc)

from dice.elements import Integer, Dice
from dice.utilities import patch_pyparsing

# Set PyParsing options
patch_pyparsing(verbose=False)

def operatorPrecedence(base, operators):
    """
    This re-implements pyparsing's operatorPrecedence function.

    It gets rid of a few annoying bugs, like always putting operators inside
    a Group, and matching the whole grammar with Forward first (there may
    actually be a reason for that, but I couldn't find it). It doesn't
    support trinary expressions, but they should be easy to add if it turns
    out I need them.
    """

    # The full expression, used to provide sub-expressions
    expression = Forward()

    # The initial expression
    last = base | Suppress('(') + expression + Suppress(')')

    def parse_operator(expr, arity, association, action=None):
        return expr, arity, association, action

    for operator in operators:
        # Use a function to default action to None
        expr, arity, association, action = parse_operator(*operator)

        # Check that the arity is valid
        if arity < 1 or arity > 2:
            raise Exception("Arity must be unary (1) or binary (2)")

        if association not in (opAssoc.LEFT, opAssoc.RIGHT):
            raise Exception("Association must be LEFT or RIGHT")

        # This will contain the expression
        this = Forward()

        # Create an expression based on the association and arity
        if association is opAssoc.LEFT:
            if arity == 1:
                operator_expression = last + OneOrMore(expr)
            elif arity == 2:
                operator_expression = last + OneOrMore(expr + last)
        elif association is opAssoc.RIGHT:
            if arity == 1:
                operator_expression = expr + this
            elif arity == 2:
                operator_expression = last + OneOrMore(this)

        # Set the parse action for the operator
        if action is not None:
            operator_expression.setParseAction(action)

        this <<= (operator_expression | last)
        last = this

    # Set the full expression and return it
    expression <<= last
    return expression


# An integer value
integer = Word(nums).setParseAction(Integer.parse).setName("integer")

# An expression in dice notation
expression = operatorPrecedence(integer, [
    (Literal('d').suppress(), 2, opAssoc.LEFT, Dice.parse),
    (Literal('d'), 1, opAssoc.RIGHT, Dice.parse_default),

    (Literal('+'), 2, opAssoc.LEFT),
    (Literal('-'), 2, opAssoc.LEFT),
    (Literal('*'), 2, opAssoc.LEFT),
    (Literal('/'), 2, opAssoc.LEFT),
]).setName("expression")

# Multiple expressions can be separated with delimiters
notation = StringStart() + delimitedList(expression, ';') + StringEnd()
notation.setName("notation")
