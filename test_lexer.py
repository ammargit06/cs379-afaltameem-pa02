"""
PA 2: The USILang Lexer -- verification suite.

Run: python test_lexer.py
Prints the Success Token only if every check below passes.
"""

import base64
import hashlib
import sys

from lexer import LexError, tokenize

ASSIGNMENT_ID = "PA02"


def get_student_id() -> str:
    """Prompt for the student's USI username; baked into the Success Token
    so a copied/shared token decodes to someone else's name, not yours."""
    student_id = input("Enter your USI username (e.g. cwill): ").strip()
    while not student_id:
        student_id = input("Username cannot be blank. Enter your USI username: ").strip()
    return student_id


def generate_token(assignment_id: str, student_id: str) -> str:
    digest = hashlib.sha256(f"CS379-{assignment_id}-{student_id}-VERIFIED".encode()).hexdigest()[:16]
    raw = f"CS379|{assignment_id}|{student_id}|PASS|{digest}"
    return base64.b64encode(raw.encode()).decode()


def print_success_banner(assignment_id: str) -> None:
    student_id = get_student_id()
    token = generate_token(assignment_id, student_id)
    print("\n" + "=" * 60)
    print(f"  ALL CHECKS PASSED -- {assignment_id}")
    print(f"  STUDENT: {student_id}")
    print("  SUCCESS TOKEN (paste this into Blackboard):")
    print(f"  {token}")
    print("=" * 60 + "\n")


def check(label: str, condition: bool, failures: list) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


def as_tuples(tokens):
    return [(t.type, t.lexeme, t.line) for t in tokens]


CASES = [
    (
        "let x = 12 + y3;",
        [("LET", "let", 1), ("IDENT", "x", 1), ("ASSIGN", "=", 1), ("NUMBER", "12", 1),
         ("PLUS", "+", 1), ("IDENT", "y3", 1), ("SEMI", ";", 1), ("EOF", "", 1)],
    ),
    (
        "let letter = 1;",
        [("LET", "let", 1), ("IDENT", "letter", 1), ("ASSIGN", "=", 1), ("NUMBER", "1", 1),
         ("SEMI", ";", 1), ("EOF", "", 1)],
    ),
    (
        "let a = 1;\nlet b = 2;",
        [("LET", "let", 1), ("IDENT", "a", 1), ("ASSIGN", "=", 1), ("NUMBER", "1", 1), ("SEMI", ";", 1),
         ("LET", "let", 2), ("IDENT", "b", 2), ("ASSIGN", "=", 2), ("NUMBER", "2", 2), ("SEMI", ";", 2),
         ("EOF", "", 2)],
    ),
    (
        "let x = 5; # a comment about x\nx = 6;",
        [("LET", "let", 1), ("IDENT", "x", 1), ("ASSIGN", "=", 1), ("NUMBER", "5", 1), ("SEMI", ";", 1),
         ("IDENT", "x", 2), ("ASSIGN", "=", 2), ("NUMBER", "6", 2), ("SEMI", ";", 2),
         ("EOF", "", 2)],
    ),
    (
        "(1 - 2) * 3 / 4;",
        [("LPAREN", "(", 1), ("NUMBER", "1", 1), ("MINUS", "-", 1), ("NUMBER", "2", 1), ("RPAREN", ")", 1),
         ("STAR", "*", 1), ("NUMBER", "3", 1), ("SLASH", "/", 1), ("NUMBER", "4", 1), ("SEMI", ";", 1),
         ("EOF", "", 1)],
    ),
    (
        "",
        [("EOF", "", 1)],
    ),
]


def main() -> int:
    failures: list = []

    print("Testing tokenize() against fixed snippets...\n")
    for source, expected in CASES:
        try:
            result = as_tuples(tokenize(source))
        except LexError as e:
            check(f"tokenize({source!r}) matches expected sequence (raised LexError: {e})", False, failures)
            continue
        check(f"tokenize({source!r}) matches expected token sequence", result == expected, failures)
        if result != expected:
            print(f"      got:      {result}")
            print(f"      expected: {expected}")

    print("\nTesting error handling...\n")
    try:
        tokenize("let x = 5 @ 3;")
        check("tokenize() raises LexError on an unrecognized character ('@')", False, failures)
    except LexError as e:
        has_char = "@" in str(e)
        has_line = "1" in str(e)
        check("tokenize() raises LexError mentioning the offending character and line", has_char and has_line, failures)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed. No token issued.")
        return 1

    print_success_banner(ASSIGNMENT_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
