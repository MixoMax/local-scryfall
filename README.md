# local-scryfall

A local Magic: The Gathering card search tool that uses Scryfall-like syntax for filtering cards.

## Query Syntax Guide

### Basic Filtering

The simplest way to search is by card name:
```
Lightning Bolt
```
This searches for cards containing "Lightning Bolt" in their name.

### Field-Specific Searches

Use the format `field:value` or `field=value` to search specific card properties:

#### Card Properties
- **Name**: `name:Lightning` or just `Lightning`
- **Type**: `type:Creature` or `t:Artifact`
- **Mana Value/CMC**: `mv:3` or `cmc=3`
- **Oracle Text**: `oracle:flying` or `o:"enters the battlefield"`
- **Power/Toughness**: `power:2` or `pow>=3`, `toughness:4` or `tou<=2`
- **Loyalty**: `loyalty:3` or `loy>=4`

#### Colors and Identity
- **Colors**: `color:R` or `c:WU` (exact colors)
- **Color Identity**: `identity:BG` or `id:WUBRG`

Color notation:
- `W` = White, `U` = Blue, `B` = Black, `R` = Red, `G` = Green
- `C` = Colorless (for colors field only)

#### Set and Rarity
- **Set**: `set:mh3` or `s:pmh3`
- **Rarity**: `rarity:rare` or `r:mythic`

#### Prices and Rankings
- **Euro Price**: `eur:5.50` or `price_euro>=10`
- **USD Price**: `usd:2.00` or `price_usd<=5`
- **EDHREC Rank**: `edhrec:1000` or `rank<=500`

#### Date and Formats
- **Release Date**: `date:2024-06-14` or `released>=2020-01-01`
- **Legal Formats**: `format:modern` or `f:commander`

#### Keywords
- **Keywords**: `keyword:flying` or `kw:trample`

### Operators

#### Comparison Operators
- `=` or `:` - Equals/contains
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `%=` - Contains (fuzzy search)

Examples:
```
mv>5          # Mana value greater than 5
pow<=2        # Power less than or equal to 2
oracle%=draw  # Oracle text contains "draw"
```

#### Color Operators
For colors and color identity, operators have special meanings:
- `=` - Exactly these colors
- `:` or `%=` - Contains these colors
- `>` - Contains these colors plus more
- `<` - Subset of these colors
- `>=` - Contains these colors or exactly these colors
- `<=` - Subset of these colors or exactly these colors

Examples:
```
c:R           # Red cards (may have other colors)
c=R           # Exactly red (mono-red)
c>=WU         # White-blue or cards with both white and blue
id<WUBRG      # Color identity is a subset of all colors
```

### Count Queries (n- prefix)

Use `n-` before a field to count elements:
```
n-colors=2    # Cards with exactly 2 colors
n-keywords>=3 # Cards with 3 or more keywords
n-set=1       # Cards in exactly 1 set
```

### Logical Operators

#### AND (implicit or explicit)
```
type:creature power>=3        # Implicit AND
type:creature AND power>=3    # Explicit AND
```

#### OR
```
rarity:rare OR rarity:mythic
c:R OR c:G
```

#### NOT (using -)
```
-type:creature              # Not creatures
type:creature -color:R      # Creatures that are not red
```

#### Parentheses for Grouping
```
type:creature AND (power>=5 OR toughness>=5)
(c:R OR c:G) AND mv<=3
```

### Complex Examples

```
# Cheap aggressive creatures
type:creature mv<=2 pow>=2 (c:R OR c:W)

# Expensive blue or black spells
(c:U OR c:B) mv>=6 -type:creature

# Modern-legal artifacts under $10
type:artifact format:modern usd<=10

# Multicolored commanders
n-colors>=2 format:commander type:legendary

# Recent expensive cards
released>=2023-01-01 usd>=20

# Low-CMC card draw spells
mv<=3 oracle:"draw" -type:creature
```

### Field Reference

| Field | Shortcuts | Description | Example Values |
|-------|-----------|-------------|----------------|
| `name` | - | Card name | "Lightning Bolt" |
| `type_line` | `t`, `type` | Full type line | "Creature — Human Wizard" |
| `cmc` | `mv`, `manavalue` | Mana value | 3.0 |
| `oracle_text` | `o`, `oracle` | Rules text | "Flying, trample" |
| `power` | `pow` | Creature power | 2.0 |
| `toughness` | `tou` | Creature toughness | 2.0 |
| `loyalty` | `loy` | Planeswalker loyalty | 4 |
| `colors` | `c`, `color` | Card colors | ["U", "R"] |
| `color_identity` | `id`, `identity`, `ci` | Commander color identity | ["W", "U"] |
| `keywords` | `kw`, `keyword` | Ability keywords | ["flying", "lifelink"] |
| `set` | `s`, `e`, `edition` | Set codes | ["mh3", "pmh3"] |
| `rarity` | `r` | Card rarity | "rare", "mythic" |
| `price_euro` | `eur` | Euro price | 4.63 |
| `price_usd` | `usd` | USD price | 1.95 |
| `legal_formats` | `f`, `format` | Legal formats | ["modern", "commander"] |
| `released_at` | `date`, `released` | Release date | "2024-06-14" |
| `edhrec_rank` | `edhrec`, `rank` | EDHREC popularity rank | 1000 |

