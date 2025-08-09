from scryfall_syntax_parser import query_to_filter, Filter, LogicalFilter, Operator, LogicalOperator, apply_filters, print_filters
from scryfall_bulk_importer import load_data
import colorama
import argparse
import time

card_data = load_data("cards.json")

TEST_CASES = [
    [
        "t:creature OR t:planeswalker cmc=4",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="creature", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="planeswalker", operator=Operator.CONTAINS)]),
                Filter(key="cmc", value=4, operator=Operator.EQUALS)])
    ],
    [
        "t:artifact AND (cmc>3 OR cmc<2)",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="artifact", operator=Operator.CONTAINS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="cmc", value=3, operator=Operator.GREATER_THAN),
                        Filter(key="cmc", value=2, operator=Operator.LESS_THAN)
                    ])
            ])
    ],
    [
        "t:enchantment",
        Filter(key="type_line", value="enchantment", operator=Operator.CONTAINS)
    ],
    [
        "t:enchantment cmc>=5",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="enchantment", operator=Operator.CONTAINS),
                Filter(key="cmc", value=5, operator=Operator.GREATER_THAN_OR_EQUAL)])
    ],
    [
        "t:creature t:elf cmc<3",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="creature", operator=Operator.CONTAINS),
                Filter(key="type_line", value="elf", operator=Operator.CONTAINS),
                Filter(key="cmc", value=3, operator=Operator.LESS_THAN)
            ])
    ],
    [
        "t:instant OR t:sorcery",
        LogicalFilter(
            operator=LogicalOperator.OR,
            filters=[
                Filter(key="type_line", value="instant", operator=Operator.CONTAINS),
                Filter(key="type_line", value="sorcery", operator=Operator.CONTAINS)
            ])
    ]
]


TEST_CASES = [
    # Original Test Cases
    [
        "t:creature OR t:planeswalker cmc=4",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="creature", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="planeswalker", operator=Operator.CONTAINS)]),
                Filter(key="cmc", value=4, operator=Operator.EQUALS)])
    ],
    [
        "t:artifact (cmc>3 OR cmc<2)", # Note: Implicit AND is assumed before the parenthesis
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="artifact", operator=Operator.CONTAINS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="cmc", value=3, operator=Operator.GREATER_THAN),
                        Filter(key="cmc", value=2, operator=Operator.LESS_THAN)
                    ])
            ])
    ],
    [
        "t:enchantment",
        Filter(key="type_line", value="enchantment", operator=Operator.CONTAINS)
    ],
    [
        "t:enchantment cmc>=5",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="enchantment", operator=Operator.CONTAINS),
                Filter(key="cmc", value=5, operator=Operator.GREATER_THAN_OR_EQUAL)])
    ],
    [
        "t:creature t:elf cmc<3",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="creature", operator=Operator.CONTAINS),
                Filter(key="type_line", value="elf", operator=Operator.CONTAINS),
                Filter(key="cmc", value=3, operator=Operator.LESS_THAN)
            ])
    ],
    [
        "t:instant OR t:sorcery",
        LogicalFilter(
            operator=LogicalOperator.OR,
            filters=[
                Filter(key="type_line", value="instant", operator=Operator.CONTAINS),
                Filter(key="type_line", value="sorcery", operator=Operator.CONTAINS)
            ])
    ],
    [
        "o:\"whenever you draw a card\"",
        Filter(key="oracle_text", value="whenever you draw a card", operator=Operator.CONTAINS)
    ],
    [
        "kw:flying",
        Filter(key="keywords", value="flying", operator=Operator.CONTAINS)
    ],
    [
        "r=rare",
        Filter(key="rarity", value="rare", operator=Operator.EQUALS)
    ],
    [
        "name=\"Birds of Paradise\"",
        Filter(key="name", value="Birds of Paradise", operator=Operator.EQUALS)
    ],
    [
        "Tarmogoyf", # Loose name word
        Filter(key="name", value="Tarmogoyf", operator=Operator.CONTAINS)
    ],
    [
        "cmc>5",
        Filter(key="cmc", value=5.0, operator=Operator.GREATER_THAN)
    ],
    [
        "pow<7",
        Filter(key="power", value=7.0, operator=Operator.LESS_THAN)
    ],
    [
        "tou>=10",
        Filter(key="toughness", value=10.0, operator=Operator.GREATER_THAN_OR_EQUAL)
    ],
    [
        "loy<=4",
        Filter(key="loyalty", value=4.0, operator=Operator.LESS_THAN_OR_EQUAL)
    ],
    [
        "year=1993",
        Filter(key="year", value=1993, operator=Operator.EQUALS)
    ],
    [
        "usd>99.99",
        Filter(key="price_usd", value=99.99, operator=Operator.GREATER_THAN)
    ],
    [
        "eur=0.50",
        Filter(key="price_euro", value=0.50, operator=Operator.EQUALS)
    ],
    [
        "s:m21",
        Filter(key="set", value="m21", operator=Operator.CONTAINS)
    ],
    [
        "e:war", # 'e' is an alias for 'set'
        Filter(key="set", value="war", operator=Operator.CONTAINS)
    ],
    [
        "f:modern",
        Filter(key="legal_formats", value="modern", operator=Operator.CONTAINS)
    ],
    [
        "c:wubrg", # Contains all 5 colors
        Filter(key="colors", value="WUBRG", operator=Operator.CONTAINS)
    ],
    [
        "c=wu", # Exactly white and blue
        Filter(key="colors", value="WU", operator=Operator.EQUALS)
    ],
    [
        "id<=wug", # Color identity is a subset of or equal to Bant (WUG)
        Filter(key="color_identity", value="WUG", operator=Operator.LESS_THAN_OR_EQUAL)
    ],
    [
        "id>=ubr", # Color identity is a superset of or equal to Grixis (UBR)
        Filter(key="color_identity", value="UBR", operator=Operator.GREATER_THAN_OR_EQUAL)
    ],
    [
        "c:c", # Colorless
        Filter(key="colors", value="C", operator=Operator.CONTAINS)
    ],
    [
        "id:c", # Colorless identity
        Filter(key="color_identity", value="C", operator=Operator.CONTAINS)
    ],
    [
        "-t:creature",
        LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="type_line", value="creature", operator=Operator.CONTAINS)])
    ],
    [
        "-c:w",
        LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="colors", value="W", operator=Operator.CONTAINS)])
    ],
    [
        "-kw:trample",
        LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="keywords", value="trample", operator=Operator.CONTAINS)])
    ],
    [
        "-(t:artifact OR t:enchantment)", # Negating a group
        LogicalFilter(
            operator=LogicalOperator.NOT,
            filters=[
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="artifact", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="enchantment", operator=Operator.CONTAINS)
                    ]
                )
            ]
        )
    ],
    [
        "t:legendary (t:goblin OR t:elf)",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="type_line", value="legendary", operator=Operator.CONTAINS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="goblin", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="elf", operator=Operator.CONTAINS)
                    ]
                )
            ]
        )
    ],
    [
        "(c:w OR c:u) (t:instant OR t:sorcery) cmc<=2",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="colors", value="W", operator=Operator.CONTAINS),
                        Filter(key="colors", value="U", operator=Operator.CONTAINS)
                    ]
                ),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="instant", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="sorcery", operator=Operator.CONTAINS)
                    ]
                ),
                Filter(key="cmc", value=2.0, operator=Operator.LESS_THAN_OR_EQUAL)
            ]
        )
    ],
    [
        "f:commander (-t:creature OR pow>5)",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="legal_formats", value="commander", operator=Operator.CONTAINS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        LogicalFilter(
                            operator=LogicalOperator.NOT,
                            filters=[Filter(key="type_line", value="creature", operator=Operator.CONTAINS)]
                        ),
                        Filter(key="power", value=5.0, operator=Operator.GREATER_THAN)
                    ]
                )
            ]
        )
    ],
    [
        "c=r AND (t:goblin OR (t:warrior AND cmc<3))", # Explicit AND
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="colors", value="R", operator=Operator.EQUALS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="goblin", operator=Operator.CONTAINS),
                        LogicalFilter(
                            operator=LogicalOperator.AND,
                            filters=[
                                Filter(key="type_line", value="warrior", operator=Operator.CONTAINS),
                                Filter(key="cmc", value=3.0, operator=Operator.LESS_THAN)
                            ]
                        )
                    ]
                )
            ]
        )
    ],
    [
        "(id:wub t:angel) OR (id:brg t:dragon)",
        
        LogicalFilter(
            operator=LogicalOperator.OR,
            filters=[
                LogicalFilter(
                    operator=LogicalOperator.AND,
                    filters=[
                        Filter(key="color_identity", value="WUB", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="angel", operator=Operator.CONTAINS)
                    ]
                ),
                LogicalFilter(
                    operator=LogicalOperator.AND,
                    filters=[
                        Filter(key="color_identity", value="BRG", operator=Operator.CONTAINS),
                        Filter(key="type_line", value="dragon", operator=Operator.CONTAINS)
                    ]
                )
            ]
        )
    ],
    [
        "c:w (t:knight OR (t:soldier (pow>2 OR tou>2)))", # Deep nesting
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="colors", value="W", operator=Operator.CONTAINS),
                LogicalFilter(
                    operator=LogicalOperator.OR,
                    filters=[
                        Filter(key="type_line", value="knight", operator=Operator.CONTAINS),
                        LogicalFilter(
                            operator=LogicalOperator.AND,
                            filters=[
                                Filter(key="type_line", value="soldier", operator=Operator.CONTAINS),
                                LogicalFilter(
                                    operator=LogicalOperator.OR,
                                    filters=[
                                        Filter(key="power", value=2.0, operator=Operator.GREATER_THAN),
                                        Filter(key="toughness", value=2.0, operator=Operator.GREATER_THAN)
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ],
    [
        # Test 38: legal commanders in izzet colors
        "f:commander ci:RU AND -t:land AND -t:stickers AND -t:attraction",
        LogicalFilter(
            operator=LogicalOperator.AND,
            filters=[
                Filter(key="legal_formats", value="commander", operator=Operator.CONTAINS),
                Filter(key="color_identity", value="RU", operator=Operator.CONTAINS),
                LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="type_line", value="land", operator=Operator.CONTAINS)]),
                LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="type_line", value="stickers", operator=Operator.CONTAINS)]),
                LogicalFilter(operator=LogicalOperator.NOT, filters=[Filter(key="type_line", value="attraction", operator=Operator.CONTAINS)]),
            ]
        )
    ]
]


def run_one_test(test_case: list):
    query, expected_filter = test_case
    got_filter = query_to_filter(query)

    _cards_expected = apply_filters(card_data, expected_filter)
    cards_expected = set([hash(str(card)) for card in _cards_expected])

    _cards_got = apply_filters(card_data, got_filter)
    cards_got = set([hash(str(card)) for card in _cards_got])

    if len(cards_expected) == 0:
        return (-1, query, expected_filter, got_filter, len(cards_expected), len(cards_got))

    if cards_expected != cards_got:
        return (0, query, expected_filter, got_filter, len(cards_expected), len(cards_got))
    else:
        return (1, query, expected_filter, got_filter, len(cards_expected), len(cards_got))


def run_tests(print_all: bool = False):
    t_start = time.time()

    n_pass = 0
    n_fail = 0
    n_warn = 0
    n_broken = 0
    
    for idx, test_case in enumerate(TEST_CASES):
        try:
            success, query, expected_filter, got_filter, n_expected, n_got = run_one_test(test_case)
            if (success == -1 or success == 0) or print_all:
                print(f"{idx + 1}/{len(TEST_CASES)} - ", end="")
                match success:
                    case 1: print(colorama.Fore.GREEN + f"PASS for query: {query} (returned {n_got} cards)" + colorama.Fore.RESET)
                    case 0: 
                        print(colorama.Fore.RED + "FAIL for query: " + query + colorama.Fore.RESET)
                        print("Expected filter: ", end="")
                        print_filters(expected_filter)
                        print(f" (expected {n_expected} cards)")
                        print()
                        print("Got filter: ", end="")
                        print_filters(got_filter)
                        print(f" (got {n_got} cards)")
                        print()
                    case -1: 
                        print(colorama.Fore.YELLOW + "WARNING for query: " + query + colorama.Fore.RESET)
                        print("Expected filter: ", end="")
                        print_filters(expected_filter)
                        print(f" (expected {n_expected} cards)")
                        print()
                        print("Got filter: ", end="")
                        print_filters(got_filter)
                        print(f" (got {n_got} cards)")
                        print("This test case is expected to return some cards, but it returned none.")
                        print()

        except Exception as e:
            success = False
            print(colorama.Fore.RED + f"Error running test {idx + 1}: {e}" + colorama.Fore.RESET)
            print(f"Test case: {test_case}")
            n_broken += 1
            continue
        match success:
            case 1: n_pass += 1
            case 0: n_fail += 1
            case -1: n_warn += 1

    t_end = time.time()
    t_delta = t_end - t_start

    print(f"Finished running tests in {t_delta:.2f} seconds.")
    print(f"tests run: {len(TEST_CASES)}")
    print(f"tests passed: {n_pass}")
    print(f"tests failed: {n_fail}")
    print(f"tests warned: {n_warn}")
    print(f"tests broken: {n_broken}")
    perc = (n_pass / len(TEST_CASES)) * 100 if len(TEST_CASES) > 0 else 0
    print(f"Success rate: {perc:.2f}%")

    if n_pass == len(TEST_CASES):
        print(colorama.Fore.GREEN + "All tests passed!" + colorama.Fore.RESET)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run syntax parser tests.")
    parser.add_argument("--all", action="store_true", help="Print all tests (including passing ones)")
    args = parser.parse_args()

    colorama.init()
    run_tests(print_all=args.all)
    colorama.deinit()
