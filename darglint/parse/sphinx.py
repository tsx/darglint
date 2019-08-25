from typing import (
    List,
)
from functools import (
    reduce,
)

from ..token import (
    Token,
    TokenType,
    KEYWORDS,
)
from .cyk import (
    parse as cyk_parse,
)
from ..node import (
    CykNode,
)
from .combinator import (
    parser_combinator,
)

from .grammars.sphinx_arguments_section import ArgumentsGrammar
from .grammars.sphinx_argument_type_section import ArgumentTypeGrammar
from .grammars.sphinx_long_description import LongDescriptionGrammar
from .grammars.sphinx_variables_section import VariablesSectionGrammar
from .grammars.sphinx_variable_type_section import VariableTypeGrammar
from .grammars.sphinx_raises_section import RaisesGrammar
from .grammars.sphinx_returns_section import ReturnsGrammar
from .grammars.sphinx_return_type_section import ReturnTypeGrammar
from .grammars.sphinx_short_description import ShortDescriptionGrammar
from .grammars.sphinx_yields_section import YieldsGrammar
from .grammars.sphinx_yield_type_section import YieldTypeGrammar


def two_newline_separated_or_keyword(tokens, i):
    # type: (List[Token], int) -> int
    newline_count = 0
    j = i
    while j < len(tokens):
        if tokens[j].token_type == TokenType.NEWLINE:
            newline_count += 1
        else:
            break
        j += 1

    if newline_count >= 2:
        return j

    if (j + 1 < len(tokens)
            and tokens[j].token_type == TokenType.COLON
            and tokens[j + 1].token_type in KEYWORDS):
        return j

    return 0


def top_parse(tokens):
    # type: (List[Token]) -> List[List[Token]]
    all_sections = list()
    curr = 0
    # Strip leading newlines.
    while curr < len(tokens) and tokens[curr].token_type == TokenType.NEWLINE:
        curr += 1
    prev = curr

    while curr < len(tokens):
        split_end = two_newline_separated_or_keyword(tokens, curr)
        if split_end > curr:
            if tokens[prev:curr]:
                all_sections.append(
                    tokens[prev:curr]
                )
            curr = split_end
            prev = curr
        else:
            curr += 1
    last_section = tokens[prev:curr]
    if last_section:
        all_sections.append(last_section)
    return all_sections


def _match(token):
    """Match the given token from the given section to a set of grammars.

    Args:
        token: The token to match.  This should hint at what sections
            could possibly be here.

    Returns:
        A list of grammars to be tried in order.

    """
    tt_lookup = {
        TokenType.VARIABLES: [
            VariablesSectionGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.ARGUMENTS: [
            ArgumentsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.ARGUMENT_TYPE: [
            ArgumentTypeGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.VARIABLE_TYPE: [
            VariableTypeGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.RAISES: [
            RaisesGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.YIELDS: [
            YieldsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.YIELD_TYPE: [
            YieldTypeGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.RETURNS: [
            ReturnsGrammar,
            LongDescriptionGrammar,
        ],
        TokenType.RETURN_TYPE: [
            ReturnTypeGrammar,
            LongDescriptionGrammar,
        ],
    }
    return tt_lookup.get(token.token_type, [LongDescriptionGrammar])


def lookup(section, section_index=-1):
    assert len(section) > 0
    if (section[0].token_type == TokenType.COLON
            and len(section) > 1):
        grammars = _match(section[1])
    else:
        grammars = [LongDescriptionGrammar]
    if section_index == 0:
        return [ShortDescriptionGrammar] + grammars
    return grammars


def combinator(*args):
    def inner(*nodes):
        if len(nodes) == 1:
            return CykNode(
                symbol='docstring',
                lchild=nodes[0],
            )
        elif len(nodes) == 2:
            return CykNode(
                symbol='docstring',
                lchild=nodes[0],
                rchild=nodes[1],
            )
    if args:
        return reduce(inner, args)
    else:
        # The arguments are empty, so we return an
        # empty docstring.
        return CykNode(symbol='docstring')


def parse(tokens):
    def mapped_lookup(section, section_index=-1):
        for grammar in lookup(section, section_index):
            yield lambda x: cyk_parse(grammar, x)
    return parser_combinator(top_parse, mapped_lookup, combinator, tokens)
