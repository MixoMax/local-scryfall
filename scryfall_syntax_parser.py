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
    "=": Operator.EQUALS,
    ">": Operator.GREATER_THAN,
    "<": Operator.LESS_THAN,
    ">=": Operator.GREATER_THAN_OR_EQUAL,
    "<=": Operator.LESS_THAN_OR_EQUAL,
    "%=": Operator.CONTAINS,
    ":": Operator.CONTAINS
}



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
        
        elif isinstance(item_value, list) and isinstance(self.value, str):
            match self.operator:
                case Operator.EQUALS:
                    return self.value in item_value
                case Operator.CONTAINS:
                    return any(self.value.lower() in str(v).lower() for v in item_value)
                case _:
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


KEY_SHORT_HANDS = { # key: short hands
    "type_line": ("t", "type"),
    "name": ("n"),
    "cmc": ("cost"),
    "keywords": ("kw"),
    "set": ("s"),
    "rarity": ("r"),
    "price_euro": ("euro", "eur"),
    "price_usd": ("usd"),
    "legal_formats": ("f", "format"),
    "power": ("pow", "p"),
    "toughness": ("tough", "to"),
    "loyalty": ("l", "loy"),
    "oracle_text": ("text", "o"),
    "colors": ("col", "c"),
    "color_identity": ("col_id", "ci"),
    "released-at": ("release", "date")
}

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
    is_in_quote = False
    new_query = ""
    for char in query:
        if char == "'" or char == '"':
            is_in_quote = not is_in_quote
        
        if char == " " and is_in_quote:
            new_query += "#"
        else:
            new_query += char
    
    parts = new_query.split()
    filters: list[Union[Filter, LogicalFilter]] = []
    for part in parts:
        part = part.strip()

        found_operator = False
        for op_symbol, op in OPERATOR_SYMBOLS.items():
            if op_symbol in part:
                found_operator = True
                key, value = part.split(op_symbol, 1)
                key = key.strip()

                for shorthand_key, shorthand_values in KEY_SHORT_HANDS.items():
                    if key in shorthand_values:
                        key = shorthand_key
                        break

                value = value.strip()
                if value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                elif value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.isdigit():
                    value = int(value)
                
                if key[0] == "-":
                    key = key[1:]
                    f = LogicalFilter(LogicalOperator.NOT, [Filter(key, value, op)])
                    if filters and isinstance(filters[-1], LogicalFilter):
                        filters[-1].add_filter(f)
                    else:
                        filters.append(f)
                else:
                    f = Filter(key, value, op)
                    if filters and isinstance(filters[-1], LogicalFilter):
                        filters[-1].add_filter(f)
                    else:
                        filters.append(f)
                break

        if not found_operator:
            # If no operator was found, treat it as a name filter or logical filter

            value = part.strip()
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            
            if value.lower() in ["and", "or"]:
                operator = LogicalOperator.AND if value.lower() == "and" else LogicalOperator.OR
                if filters:
                    last_filter = filters.pop()
                    if isinstance(last_filter, LogicalFilter):
                        last_filter.operator = operator
                        filters.append(last_filter)
                    else:
                        filters.append(LogicalFilter(operator, [last_filter], debug_print))
            else:
                # Assume it's a name filter
                filters.append(Filter("name", value, Operator.CONTAINS))
                
    if not filters:
        raise ValueError("No valid filters found in query")
    
    if len(filters) == 1:
        return filters[0]
    else:
        # Combine all filters into a single LogicalFilter with AND operator
        return LogicalFilter(LogicalOperator.AND, filters, debug_print)
    

    



                

        
        
            

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
