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

OPERATOR_SYMBOLS = {
    ">=": Operator.GREATER_THAN_OR_EQUAL,
    "<=": Operator.LESS_THAN_OR_EQUAL,
    "%=": Operator.CONTAINS,
    "=": Operator.EQUALS,
    ">": Operator.GREATER_THAN,
    "<": Operator.LESS_THAN,
    ":": Operator.CONTAINS
}




class Filter:
    def __init__(self, key: str, value, operator: Operator = Operator.EQUALS, debug_print: bool = False, is_n_key: bool = False):
        self.debug_print = debug_print
        self.key = key
        self.value = value
        self.operator = operator
        self.is_n_key = is_n_key
    
    def check(self, item: dict) -> bool:
        if self.key not in item:
            return False
        
        item_value = item[self.key]

        if self.is_n_key:
            if isinstance(item_value, (str, list)):
                item_value = len(item_value)
            else:
                item_value = 0
        
        if isinstance(item_value, str) and isinstance(self.value, str):
            match self.operator:
                case Operator.EQUALS:
                    return item_value == self.value
                case Operator.CONTAINS:
                    return self.value.lower() in item_value.lower()
                case _:
                    raise ValueError(f"Unsupported operator for string comparison: {self.operator}")
        
        elif isinstance(item_value, list) and isinstance(self.value, str):
            if self.key == "colors" or self.key == "color_identity":
                search_value = self.value.upper()
                is_searching_for_colorless = "C" in search_value
                search_value = [char for char in search_value if char != "C"]
                match self.operator:
                    case Operator.EQUALS:
                        return set(search_value) == set(item_value)
                    case Operator.CONTAINS:
                        match self.key:
                            case "color_identity":
                                printd(self.debug_print, f"Checking color identity: {item_value} against {search_value}")
                                return all([v in search_value for v in item_value])
                            case "colors":
                                printd(self.debug_print, f"Checking colors: {item_value} against {search_value}")
                                return all(v in item_value for v in search_value) or (is_searching_for_colorless and len(item_value) == 0)
                    case Operator.GREATER_THAN:
                        return all(v in item_value for v in search_value) and len(item_value) > len(search_value)
                    case Operator.LESS_THAN:
                        return all([v in search_value for v in item_value]) and len(item_value) < len(search_value)
                    case Operator.GREATER_THAN_OR_EQUAL:
                        printd(self.debug_print, f"Checking greater than or equal: {item_value} against {search_value}")
                        return (all(v in item_value for v in search_value) and len(item_value) > len(search_value)) or set(search_value) == set(item_value)
                    case Operator.LESS_THAN_OR_EQUAL:
                        printd(self.debug_print, f"Checking less than or equal: {item_value} against {search_value}")
                        return (all(v in search_value for v in item_value) and len(item_value) < len(search_value)) or set(search_value) == set(item_value)
            else:
                match self.operator:
                    case Operator.EQUALS | Operator.CONTAINS:
                        return any(self.value.lower() in str(v).lower() for v in item_value)
                    case Operator.GREATER_THAN | Operator.LESS_THAN | Operator.GREATER_THAN_OR_EQUAL | Operator.LESS_THAN_OR_EQUAL:
                        raise ValueError(f"Unsupported operator for list comparison: {self.operator}")
            
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
        n_prefix = "n-" if self.is_n_key else ""
        return f"Filter(key={n_prefix}{self.key}, value={self.value}, operator={self.operator})"
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


KEY_SHORT_HANDS = { # key: short hands
    "type_line": ("t", "type"),
    "name": ("name",),
    "cmc": ("mv", "manavalue"),
    "keywords": ("kw", "keyword"),
    "set": ("s", "e", "set", "edition"),
    "rarity": ("r", "rarity"),
    "price_euro": ("eur",),
    "price_usd": ("usd",),
    "legal_formats": ("f", "format"),
    "power": ("pow", "power"),
    "toughness": ("tou", "toughness"),
    "loyalty": ("loy", "loyalty"),
    "oracle_text": ("o", "oracle"),
    "colors": ("c", "color"),
    "color_identity": ("id", "identity", "ci"),
    "released_at": ("date", "released"),
    "edhrec_rank": ("edhrec", "rank", "edhrec_rank"),
}

def query_to_filter(query: str, debug_print: bool = False) -> Union[Filter, LogicalFilter]:
    # Pre-process query to make parsing easier
    query = query.replace("(", " ( ").replace(")", " ) ")
    # Tokenize query, respecting quotes
    tokens = [t for t in re.split(r'\s+(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)', query.strip()) if t]

    def parse_expression(tokens):
        # Lowest precedence: implicit AND
        and_operands = []
        while tokens:
            and_operands.append(parse_term(tokens))
            if tokens and tokens[0].upper() == 'AND':
                tokens.pop(0)  # Consume 'AND'
            elif tokens and tokens[0] not in [')', 'OR']:
                # Implicit AND
                pass
            else:
                break
        
        if len(and_operands) > 1:
            return LogicalFilter(LogicalOperator.AND, and_operands, debug_print)
        return and_operands[0]

    def parse_term(tokens):
        # Higher precedence: OR
        or_operands = []
        while tokens:
            or_operands.append(parse_factor(tokens))
            if tokens and tokens[0].upper() == 'OR':
                tokens.pop(0)  # Consume 'OR'
            else:
                break
        
        if len(or_operands) > 1:
            return LogicalFilter(LogicalOperator.OR, or_operands, debug_print)
        return or_operands[0]

    def parse_factor(tokens):
        token = tokens.pop(0)
        is_negated = False
        if token == '-':
            is_negated = True
            token = tokens.pop(0)
        elif token.startswith('-') and len(token) > 1:
            is_negated = True
            token = token[1:]

        if token == '(':
            expr = parse_expression(tokens)
            if not tokens or tokens.pop(0) != ')':
                raise ValueError("Mismatched parentheses")
            if is_negated:
                return LogicalFilter(LogicalOperator.NOT, [expr], debug_print)
            return expr

        # It's a simple filter
        filter_expr = parse_simple_filter(token)
        if is_negated:
            return LogicalFilter(LogicalOperator.NOT, [filter_expr], debug_print)
        return filter_expr

    def parse_simple_filter(token):
        for op_symbol, op in OPERATOR_SYMBOLS.items():
            if op_symbol in token:
                key, value = token.split(op_symbol, 1)

                is_n_key = False
                if key.startswith('n-') and len(key) > 2:
                    is_n_key = True
                    key = key[2:]

                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                if value.replace('.', '', 1).isdigit():
                    num = float(value)
                    if op == Operator.EQUALS and num.is_integer():
                        value = int(num)
                    else:
                        value = num
                
                original_key = key
                for k, shorthands in KEY_SHORT_HANDS.items():
                    if key in shorthands:
                        key = k
                        break
                
                return Filter(key, value, op, debug_print, is_n_key=is_n_key)
        
        return Filter("name", token, Operator.CONTAINS, debug_print)

    return parse_expression(tokens)
    

    



                

        
        
            

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
