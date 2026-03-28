# tir-pukiwiki

PukiWiki <-> TIR converter backend for tirenvi.

## Install

```bash
pip install tir-pukiwiki
```

## Usage

```bash
tir-pukiwiki parse file.pukiwiki > file.tir
tir-pukiwiki unparse file.pukiwiki < file.tir
```

## Note

- All tables are converted to PukiWiki table format on unparse (not CSV-style tables)
- | inside a cell is replaced with ｜ (full-width pipe)
- This behavior can be changed with the --pipe option
