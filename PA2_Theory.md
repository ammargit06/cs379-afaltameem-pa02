# PA 2: The USILang Lexer — Part A: The Specification

CS 379: Programming Languages (Fall 2026)

---

## 1. Regex Design (15 pts)

### The patterns

| Terminal category | Python regular expression |
|---|---|
| `NUMBER` | `[0-9]+` |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*` |
| whitespace | `[ \t\r\n]+` (in the lexer this is split into `[ \t\r]+` for plain spacing and `\n` on its own, so a newline can bump the line counter before it is discarded) |

`NUMBER` is `[0-9]+` — one or more decimal digits, nothing else. The Week 2
`usilang.bnf` defines `NUMBER` as an *unsigned integer*, so there is no
decimal point, sign, or exponent to match. `[0-9]+` also happily accepts
leading zeros (`007`), which USILang allows.

`IDENT` is `[A-Za-z_][A-Za-z0-9_]*` — a leading letter or underscore, then
zero or more letters, digits, or underscores. The first character class
deliberately excludes digits so that a digit can never *start* an
identifier; the trailing `*` (Kleene star, zero-or-more) is what lets `x1`,
`y3`, and `letter` each stay a single token instead of splitting.

whitespace is "one or more" spacing characters. It is recognized so the
scanner knows where a token ends, but it is never turned into a `Token`.

### Maximal munch (the longest-match rule)

Maximal munch means: at each position in the source, the lexer consumes the
**longest** run of characters that still forms a valid lexeme for some
token, and only then emits a token and moves on. It does not stop at the
first point where it *could* emit something — it keeps extending the match
as long as the next character can legally be part of the current lexeme.
So `123` is one `NUMBER("123")`, not three `NUMBER` tokens, and `y3` is one
`IDENT("y3")`, not `IDENT("y")` followed by `NUMBER("3")`. The scan only
stops when the next character has no valid edge to follow (a space, a `;`,
end of input, an illegal character, …).

### Why alternative order matters for `let` vs. `letter`

The rule that guarantees `letter` is never mis-tokenized as `LET` +
`IDENT("ter")` is **"match the wide `IDENT` pattern first, then downgrade,"**
not "check keywords first."

If instead you put a literal keyword alternative ahead of `IDENT` in the
master pattern — `(?P<LET>let)|(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)` — then on
the input `letter` the regex engine can match the `LET` alternative against
just the first three characters `let`, succeed, and return a `LET` token,
leaving `ter` behind to be scanned next as `IDENT("ter")`. Whether that
actually happens depends on the engine's alternation and backtracking
behavior, which makes the approach fragile and engine-dependent. Ordering
a *narrow* literal pattern first does **not** save you.

The safe strategy, and the one my lexer uses:

1. Have exactly one identifier-shaped alternative, the wide
   `IDENT` pattern `[A-Za-z_][A-Za-z0-9_]*`. Maximal munch forces it to
   consume the **entire** run `letter` — it cannot stop early at `let`,
   because `t`, `e`, `r` are all valid identifier characters.
2. **After** the match, check the resulting lexeme against a reserved-word
   set `{"let"}`. If the whole lexeme is exactly `let`, relabel the token
   `LET`; otherwise it stays `IDENT`.

Because step 1 always grabs the longest identifier and step 2 only relabels
when the *entire* lexeme equals a reserved word, `let` → `LET`,
`letter` → `IDENT("letter")`, and the same one rule silently protects every
other keyword/identifier collision (`if`/`iffy`, `for`/`format`, …) with no
new code.

---

## 2. Hand Tokenization (15 pts)

Source line (line 1): `let x = 12 + y3;`

| # | (type, lexeme, line) | Why |
|---|---|---|
| 1 | `("LET", "let", 1)` | `[A-Za-z_]\w*` munches `let`; space ends it; whole lexeme is in the reserved set, so `IDENT` is downgraded to `LET`. |
| 2 | `("IDENT", "x", 1)` | `x` is a single-letter identifier; the space after it ends the munch. |
| 3 | `("ASSIGN", "=", 1)` | Single `=`; USILang has no `==`. |
| 4 | `("NUMBER", "12", 1)` | `[0-9]+` munches both digits; the space ends it. |
| 5 | `("PLUS", "+", 1)` | Single `+`. |
| 6 | `("IDENT", "y3", 1)` | Identifier starts with the letter `y`, then `3` is a valid continuation char, so `y3` is **one** `IDENT` token — the `3` does **not** split off. Not in the reserved set, so it stays `IDENT`. |
| 7 | `("SEMI", ";", 1)` | Single `;`. |
| 8 | `("EOF", "", 1)` | End of input; empty lexeme; line is still 1 (no newline was seen). |

Full ordered stream (8 tokens):

```
LET("let", 1)
IDENT("x", 1)
ASSIGN("=", 1)
NUMBER("12", 1)
PLUS("+", 1)
IDENT("y3", 1)
SEMI(";", 1)
EOF("", 1)
```

Every space is read (so the scanner knows where each token ends) and then
discarded; no whitespace token appears in the stream.

---

## 3. The Maximal Munch Edge Case (10 pts)

**`12x` tokenizes as two valid tokens: `NUMBER("12")` followed by
`IDENT("x")`. It is *not* a single malformed token.**

Justification from maximal munch: scanning starts at `1`. The only token
pattern whose first character can be a digit is `NUMBER` = `[0-9]+`, so the
scanner is committed to building a `NUMBER`. It munches `1`, then `2`, then
looks at `x`. `x` is not in `[0-9]`, so the `NUMBER` munch cannot be
extended — the machine "falls off" the accepting state and emits
`NUMBER("12")`. The scan then restarts fresh at `x`. Now the `IDENT`
pattern `[A-Za-z_][A-Za-z0-9_]*` applies; it munches `x` and stops at end
of input, emitting `IDENT("x")`. At no point is there a rule that says "a
digit run immediately followed by a letter is illegal," so no `LexError` is
raised and no single fused token is produced. Both tokens are individually
well-formed, so the lexer's job here is done correctly.

Why "two tokens" is still dangerous for the language designer: the lexer
has now handed the parser a stream — `NUMBER("12")`, `IDENT("x")` — that
*looks* perfectly well-formed, but almost certainly is not what the
programmer meant. `12x` is very likely a typo for `12 * x` (a
multiplication) or `12 x` (two things that were meant to be separated). By
silently accepting it, the lexer defers the problem: the parser will fail
later, at a `NUMBER` directly abutting an `IDENT` with no operator between
them, and the resulting syntax error points at a location that no longer
obviously corresponds to the original typo. The mistake surfaces far from
its cause and is harder to trace back. This is the lexer's job being
**correct but not forgiving** — it faithfully reports what the characters
say, even when that is probably a mistake, and leaves the "is this a
sensible program" judgment to the parser and later stages.

---

## 4. Throughput Reasoning (10 pts)

My lexer does **single-pass, inline discard**. It never builds a `Token`
object for whitespace or comments and never re-scans the source.

How it works: there is one compiled master regex with named groups —
including `NEWLINE`, `SKIP` (spaces/tabs/`\r`), and `COMMENT` (`#` to end of
line) as ordinary alternatives alongside `NUMBER`, `IDENT`, the operators,
etc. A single position index `pos` walks the source once, left to right.
At each step, `Pattern.match(source, pos)` classifies the next lexeme in
one C-level regex operation, `pos` jumps forward by the length of whatever
matched, and the loop inspects `m.lastgroup`:

- `NEWLINE` → increment the line counter, emit nothing.
- `SKIP` / `COMMENT` → `continue`; emit nothing, allocate nothing.
- everything real → append one `Token`.

So whitespace and comments are recognized and thrown away *during* the scan,
without a token object ever existing for them. The alternative design —
emit `WHITESPACE`/`COMMENT` tokens and filter them out in a second pass — is
strictly more work: it allocates objects that are immediately discarded,
and it forces a second traversal of the token list.

Why more efficient at the character-stream level: every character is
touched exactly once. There is no backtracking and no second read. The
work is O(n) in the length of the source with a small constant, and memory
holds only the tokens you actually keep. Filtering afterward would still be
O(n) for the scan **plus** O(number of tokens) for the filter pass, plus
the churn of creating and garbage-collecting throwaway whitespace tokens —
for source that is often 20–40% whitespace, that is a lot of allocation for
nothing.

Why re-scanning the source string more than once is a design smell: the
lexer is the one stage that has to look at raw characters, and the whole
point of finite-state / regex scanning is that one forward pass is
*sufficient* — the current position plus the current match fully determine
the next step, so there is never a reason to go back. If a lexer re-reads
the source (for example, `re.match(pattern, text[pos:])` in a loop, which
re-slices — copies — the entire tail of the string on every iteration, or a
first pass that strips comments and a second that tokenizes), it has turned
an O(n) problem into O(n²) or two O(n) passes for no gain in what it can
recognize. That extra scanning buys nothing a single pass with one
position index and one compiled pattern does not already give you, so its
presence signals the design has drifted away from the finite-state model
the stage is supposed to embody.

---

## Appendix: the master pattern used in `lexer.py`

```python
_TOKEN_SPEC = [
    ("NUMBER",   r"[0-9]+"),
    ("IDENT",    r"[A-Za-z_][A-Za-z0-9_]*"),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("STAR",     r"\*"),
    ("SLASH",    r"/"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("ASSIGN",   r"="),
    ("SEMI",     r";"),
    ("COMMENT",  r"#[^\n]*"),
    ("NEWLINE",  r"\n"),
    ("SKIP",     r"[ \t\r]+"),
    ("MISMATCH", r"."),
]

_MASTER_RE = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_SPEC)
)

KEYWORDS = {"let": "LET"}   # IDENT matched wide, then downgraded here
```
