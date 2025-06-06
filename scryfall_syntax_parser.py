import re
import sys
from enum import Enum
from typing import Union

def printd(debug_print: bool, *args, **kwargs):
    if debug_print:
        print(*args, **kwargs)
    else:
        #TODO: log instead of printing (eventually)
        pass

class Operator(Enum):
    EQUALS = "=" # checks equality (both numbers and strings)

    # Math operators
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="

    # String fuzzy operators
    CONTAINS = "%="



class Filter:
    def __init__(self, key: str, value, operator: Operator = Operator.EQUALS):
        self.key = key
        self.value = value
        self.operator = operator
    
    def check(self, item: dict) -> bool:
        if self.key not in item:
            return False
        
        item_value = item[self.key]
        
        if isinstance(item_value, str) and isinstance(self.value, str):
            match self.operator:
                case Operator.EQUALS:
                    return item_value == self.value
                case Operator.CONTAINS:
                    return self.value.lower() in item_value.lower()
                case _:
                    raise ValueError(f"Unsupported operator for string comparison: {self.operator}")
        
        elif isinstance(item_value, (int, float)) and isinstance(self.value, (int, float)):
            match self.operator:
                case Operator.EQUALS:
                    return item_value == self.value
                case Operator.GREATER_THAN:
                    return item_value > self.value
                case Operator.LESS_THAN:
                    return item_value < self.value
                case Operator.GREATER_THAN_OR_EQUAL:
                    return item_value >= self.value
                case Operator.LESS_THAN_OR_EQUAL:
                    return item_value <= self.value
                case _:
                    raise ValueError(f"Unsupported operator for numeric comparison: {self.operator}")
        else:
            return False  # Type mismatch or unsupported comparison

    def __str__(self):
        return f"Filter(key={self.key}, value={self.value}, operator={self.operator})"
    def __repr__(self):
        return self.__str__()


class LogicalOperator(Enum):
    AND = "AND"
    NOT = "NOT"
    OR = "OR"

class LogicalFilter:
    def __init__(self, operator: LogicalOperator, filters: list[Union[Filter, 'LogicalFilter']] | None = None, debug_print: bool = False):
        self.operator = operator
        self.filters = filters if filters is not None else []
        self.debug_print = debug_print

    def add_filter(self, filter: Union[Filter, 'LogicalFilter']):
        self.filters.append(filter)
    
    def check(self, item: dict) -> bool:
        if not self.filters:
            printd(self.debug_print, "No filters to check, returning True")
            return True
        
        if self.operator == LogicalOperator.AND:
            for f in self.filters:
                if not f.check(item):
                    printd(self.debug_print, f"Filter {f} did not match item {item} for AND operation, returning False")
                    return False
            printd(self.debug_print, "All filters matched for AND operation, returning True")
            return True


        elif self.operator == LogicalOperator.OR:
            for f in self.filters:
                if f.check(item):
                    printd(self.debug_print, f"Filter {f} matched item {item} for OR operation, returning True")
                    return True
            printd(self.debug_print, "No filters matched for OR operation, returning False")
            return False


        elif self.operator == LogicalOperator.NOT:
            if len(self.filters) != 1:
                raise ValueError("NOT operator requires exactly one filter")
            return not self.filters[0].check(item)
        else:
            raise ValueError(f"Unsupported logical operator: {self.operator}")
    
    def __str__(self):
        filters_str = ", ".join(str(f) for f in self.filters)
        return f"LogicalFilter(operator={self.operator}, filters=[{filters_str}])"
    def __repr__(self):
        return self.__str__()


def apply_filters(data: list[dict], filter: Union[Filter, LogicalFilter]) -> list[dict]:
    return [item for item in data if filter.check(item)]


def query_to_filter(query: str, debug_print: bool = False) -> Union[Filter, LogicalFilter]:
    """
    Parses a query string into a Filter or LogicalFilter object.
    The query string should be in the Scryfall syntax format.
    Examples:
        --- 1)
        query = "t:creature OR t:planeswalker cmc:4"
        returns:
        LogicalFilter(
            LogicalOperator.AND,
            [
                LogicalFilter(
                    LogicalOperator.OR,
                    [
                        Filter("type_line", Operator.CONTAINS, "creature"),
                        Filter("type_line", Operator.CONTAINS, "planeswalker"),
                    ],
                ),
                Filter("cmc", Operator.EQUALS, 4),
            ]
        )

        --- 2)
        query = "t:artifact AND (cmc>3 OR cmc<2)"
        returns:
        LogicalFilter(
            LogicalOperator.AND,
            [
                Filter("type_line", Operator.CONTAINS, "artifact"),
                LogicalFilter(
                    LogicalOperator.OR,
                    [
                        Filter("cmc", Operator.GREATER_THAN, 3),
                        Filter("cmc", Operator.LESS_THAN, 2),
                    ],
                ),
            ]
        )

        --- 3)
        query = "-t:land"
        returns:
        LogicalFilter(
            LogicalOperator.NOT,
            [
                Filter("type_line", Operator.CONTAINS, "land"),
            ]
        )

        --- 4)
        query = "-t:artifact -t:creature cmc<3"
        returns:
        LogicalFilter(
            LogicalOperator.AND,
            [
                LogicalFilter(
                    LogicalOperator.NOT,
                    [
                        Filter("type_line", Operator.CONTAINS, "artifact"),
                    ],
                ),
                LogicalFilter(
                    LogicalOperator.NOT,
                    [
                        Filter("type_line", Operator.CONTAINS, "creature"),
                    ],
                ),
                Filter("cmc", Operator.LESS_THAN, 3),
            ]
        )

        --- 5)
        query = "name:'Lightning Bolt' cmc=1"
        returns:
        LogicalFilter(
            LogicalOperator.AND,
            [
                Filter("name", Operator.EQUALS, "Lightning Bolt"),
                Filter("cmc", Operator.EQUALS, 1),
            ]
        )

        --- 6)
        query = "Ur-Dragon t:legendary"
        returns:
        LogicalFilter(
            LogicalOperator.AND,
            [
                Filter("name", Operator.CONTAINS, "Ur-Dragon"),
                Filter("type_line", Operator.CONTAINS, "legendary"),
            ]
        ) 
    """
    # ---- tokenizer ----
    token_spec = [
        ("LPAREN",    r"\("),
        ("RPAREN",    r"\)"),
        ("AND",       r"\bAND\b"),
        ("OR",        r"\bOR\b"),
        ("NOT",       r"-"),
        ("TERM",      r"[^\s()]+"),
        ("SPACE",     r"\s+"),
    ]
    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec)
    tokens = []
    for mo in re.finditer(tok_regex, query):
        kind = mo.lastgroup
        if kind == "SPACE":
            continue
        tokens.append((kind, mo.group()))

    # parser state
    idx = 0
    def peek():
        return tokens[idx] if idx < len(tokens) else (None, None)
    def advance():
        nonlocal idx
        tok = tokens[idx]
        idx += 1
        return tok

    # ---- parsing ----
    def parse_expression():
        node = parse_and()
        while True:
            kind, _ = peek()
            if kind == "OR":
                advance()
                right = parse_and()
                node = LogicalFilter(LogicalOperator.OR, [node, right], debug_print)
            else:
                break
        return node

    def parse_and():
        nodes = [parse_not()]
        while True:
            kind, _ = peek()
            # implicit AND if next is TERM/LPAREN/NOT or explicit AND
            if kind in ("AND", "TERM", "LPAREN", "NOT"):
                if kind == "AND":
                    advance()
                # if it's term/paren/NOT without 'AND', treat as implicit AND
                right = parse_not()
                nodes.append(right)
            else:
                break
        if len(nodes) == 1:
            return nodes[0]
        return LogicalFilter(LogicalOperator.AND, nodes, debug_print)

    def parse_not():
        kind, val = peek()
        if kind == "NOT":
            advance()
            child = parse_not()
            return LogicalFilter(LogicalOperator.NOT, [child], debug_print)
        return parse_atom()

    def parse_atom():
        kind, val = peek()
        if kind == "LPAREN":
            advance()
            node = parse_expression()
            # consume RPAREN
            if peek()[0] == "RPAREN":
                advance()
            return node
        if kind == "TERM":
            advance()
            return make_filter(val)
        raise ValueError(f"Unexpected token: {val}")

    # ---- term→Filter conversion ----
    def make_filter(term: str) -> Union[Filter, LogicalFilter]:
        # raw word → name contains
        m = re.match(r"^([a-zA-Z_]+)(>=|<=|>|<|=|:)(.+)$", term)
        if not m:
            # bare word → CONTAINS name
            return Filter("name", term, Operator.CONTAINS)
        key, op, raw = m.groups()
        # strip quotes
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            val = raw[1:-1]
            is_str = True
        else:
            # try numeric
            try:
                val = int(raw)
                is_str = False
            except ValueError:
                try:
                    val = float(raw)
                    is_str = False
                except ValueError:
                    val = raw
                    is_str = True

        # map operator
        if op == ":":
            op_enum = Operator.CONTAINS if is_str else Operator.EQUALS
        elif op == "=":
            op_enum = Operator.EQUALS
        elif op == ">":
            op_enum = Operator.GREATER_THAN
        elif op == "<":
            op_enum = Operator.LESS_THAN
        elif op == ">=":
            op_enum = Operator.GREATER_THAN_OR_EQUAL
        elif op == "<=":
            op_enum = Operator.LESS_THAN_OR_EQUAL
        else:
            raise ValueError(f"Unknown operator: {op}")

        SHORT_KEYS = {
            "type_line": ("t", "type"),
            "name": ("n"),
            "cmc": (),
            "power": ("p", "pow"),
            "toughness": ("to", "tou"),
            "loyalty": ("l", "loy"),
            "oracle_text": ("o", "text"),
            "mana_cost": ("mc", "cost", "m", "mana"),
        }

        # map key aliases
        for field, aliases in SHORT_KEYS.items():
            if key in aliases:
                key = field
                break

        # string fuzzy for unquoted name searches
        if is_str and key.lower() == "name" and op == ":":
            op_enum = Operator.CONTAINS
        return Filter(field, val, op_enum)

    # ---- run parser ----
    root = parse_expression()
    # if only one Filter, return it directly
    return root

def print_filters(filter_expr: Union[Filter, LogicalFilter]) -> None:
    """
    Prints the filter expression using symbols: AND '^', OR 'v', NOT '¬'
    """
    def _format(expr):
        if isinstance(expr, Filter):
            key = 't' if expr.key == 'type_line' else expr.key
            return f"{key}{expr.operator.value}{expr.value}"
        if isinstance(expr, LogicalFilter):
            if expr.operator == LogicalOperator.NOT:
                sub = _format(expr.filters[0])
                if isinstance(expr.filters[0], LogicalFilter):
                    sub = f"({sub})"
                return f"¬{sub}"
            sep = ' ^ ' if expr.operator == LogicalOperator.AND else ' v '
            parts = []
            for subf in expr.filters:
                s = _format(subf)
                if isinstance(subf, LogicalFilter) and subf.operator != expr.operator:
                    s = f"({s})"
                parts.append(s)
            return sep.join(parts)
        raise ValueError(f"Unknown expression type: {expr}")
    print(_format(filter_expr))
