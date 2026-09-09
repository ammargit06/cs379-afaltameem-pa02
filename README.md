# PA 2: The USILang Lexer

Full assignment: `PA_02_The_USILang_Lexer.md`.

## Run
```bash
python test_lexer.py
```
Complete `tokenize()` in `lexer.py` using a single compiled master
regex. The harness diffs your output against exact expected
`(type, lexeme, line)` sequences across several snippets, including a
`let`/`letter` collision case and a comment/multi-line case. Success
Token prints once every check passes.

## Submit
1. `PA2_Theory.pdf` (or `.md`)
2. `lexer.py`
3. The Success Token
