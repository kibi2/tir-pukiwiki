#!/usr/bin/env python3

import sys
import json
import csv
from typing import Optional, Iterable, TypedDict

FORMAT_VERSION = "tir/0.1"


class Table(TypedDict):
    cells: list[str]
    suffix: str


# ------------------------------------------------------------
# utilities
# ------------------------------------------------------------


def read_lines(path):
    if path is None or path == "-":
        return sys.stdin.read().splitlines()
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def write_lines(path: Optional[str], lines: Iterable[str]) -> None:
    output = "\n".join(lines)
    if path is None or path == "-":
        sys.stdout.write(output)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=False))


# ------------------------------------------------------------


def is_csv_line(line: str) -> bool:
    if len(line) <= 1:
        return False
    return line.startswith(",")


def parse_pipe(line: str) -> Table:
    suffix = ""
    if line.endswith("|c"):
        line = line[:-2] + "|"
        suffix = "c"
    elif line.endswith("|h"):
        line = line[:-2] + "|"
        suffix = "h"
    elif line.endswith("|f"):
        line = line[:-2] + "|"
        suffix = "f"
    core = line
    if core.startswith("|"):
        core = core[1:]
    else:
        return {"cells": [], "suffix": ""}
    if core.endswith("|"):
        core = core[:-1]
    else:
        return {"cells": [], "suffix": ""}
    if not core:
        return {"cells": [], "suffix": ""}
    cells = core.split("|") if core else []
    cells = [c.strip() for c in cells]
    return {
        "cells": cells,
        "suffix": suffix,
    }


def split_csv_row(line: str) -> list[str]:
    core = line[1:]
    cells = next(csv.reader([core]))
    cells = [c.strip() for c in cells]
    # "==" -> ">"
    cells = [">" if c == "==" else c for c in cells]
    return cells


def input_col_count_pukiwiki(line: str) -> int:
    tmp = line
    if tmp.endswith("|c") or tmp.endswith("|h") or tmp.endswith("|f"):
        tmp = tmp[:-2] + "|"

    return tmp.count("|") - 1


def normalize_cells(cells: list[str], ncol: int) -> list[str]:
    if len(cells) < ncol:
        cells += [""] * (ncol - len(cells))
    elif len(cells) > ncol:
        cells = cells[:ncol]
    return cells


# ------------------------------------------------------------
# parse : pukiwiki -> TIR
# ------------------------------------------------------------


def print_attr_file():
    print_json(
        {
            "kind": "attr_file",
            "version": FORMAT_VERSION,
        }
    )


def print_plain(line: str):
    print_json(
        {
            "kind": "plain",
            "line": line,
        }
    )


def print_grid(row: list[str]):
    print_json(
        {
            "kind": "grid",
            "row": row,
        }
    )


def has_p_suffix(records):
    for index, record in enumerate(records):
        if record["suffix"]:
            return True
    return False


def flush_pain(records):
    for index, record in enumerate(records):
        print_plain(record)


def flush_csv(records):
    for index, record in enumerate(records):
        print_grid(record)


def flush_pipe(records):
    ncol = len(records[0]["cells"])
    has_suffix = has_p_suffix(records)
    for index, record in enumerate(records):
        suffix = record["suffix"]
        cells = record["cells"]
        if has_suffix:
            if suffix:
                cells.append(suffix)
            else:
                cells.append("")
        print_grid(cells)


def flush_p(kind):
    global records
    if len(records) == 0:
        return
    if kind == "plain":
        flush_pain(records)
    elif kind == "csv":
        flush_csv(records)
    elif kind == "pipe":
        flush_pipe(records)
    records = []


def append_p_record(kind, ncol, record):
    global prev_kind, prev_ncol, records
    if kind != prev_kind or ncol != prev_ncol:
        flush_p(prev_kind)
    if prev_ncol and ncol:
        if prev_ncol != ncol or prev_kind != kind:
            print_plain("")
    prev_kind = kind
    prev_ncol = ncol
    records.append(record)


def parse(path=None):
    global prev_kind, prev_ncol, records
    lines = read_lines(path)
    print_attr_file()
    prev_kind = None
    prev_ncol = None
    records = []
    for index, line in enumerate(lines):
        record = parse_pipe(line)
        pipe_cells = record["cells"]
        ncol = len(pipe_cells)
        if ncol > 0:
            append_p_record("pipe", ncol, record)
        elif is_csv_line(line):
            csv_cells = split_csv_row(line)
            ncol = len(csv_cells)
            append_p_record("csv", ncol, csv_cells)
        else:
            ncol = None
            append_p_record("plain", 0, line)
        # print_json(records)
    flush_p(prev_kind)


# ------------------------------------------------------------
# unparse : TIR -> pukiwiki
# ------------------------------------------------------------


def escape_cell(cell: str) -> str:
    global pipe
    return cell.replace("|", pipe)


def format_pukiwiki_row(row: list[str], suffix) -> str:
    cells = [escape_cell(c) for c in row]
    line = "|" + "|".join(cells) + "|"
    if suffix:
        line += suffix
    return line


def has_w_suffix(records):
    has_suffix = False
    for index, record in enumerate(records):
        row = record.get("row")
        if not row:
            continue
        cell = row[-1]
        if not cell:
            pass
        elif cell in ("c", "h", "f"):
            has_suffix = True
        else:
            return False
    return has_suffix


def flush_w_pain(records):
    global out_lines
    for index, record in enumerate(records):
        line = record.get("line")
        out_lines.append(line)


def flush_grid(records):
    global out_lines
    has_suffix = has_w_suffix(records)
    for index, record in enumerate(records):
        row = record.get("row")
        suffix = ""
        if has_suffix:
            suffix = row.pop()
        line = format_pukiwiki_row(row, suffix)
        out_lines.append(line)


def flush_w(records):
    if len(records) == 0:
        return
    kind = records[0].get("kind")
    if kind == "plain":
        flush_w_pain(records)
    elif kind == "grid":
        flush_grid(records)
    records.clear()


def append_w_record(records, record):
    prev_kind = None
    if records:
        prev_kind = records[-1].get("kind")
    if record.get("kind") != prev_kind:
        flush_w(records)
    records.append(record)


def unparse(path=None):
    global out_lines
    out_lines = []
    records = []
    for index, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        record = json.loads(line)
        append_w_record(records, record)
    flush_w(records)
    write_lines(path, out_lines)


# ------------------------------------------------------------
# utilities
# ------------------------------------------------------------

from importlib.metadata import version


def get_version():
    return version("tir-pukiwiki")


def usage() -> None:
    print(
        f"""tir-pukiwiki {get_version()}

usage:
  tir-pukiwiki parse   [file|-]
  tir-pukiwiki unparse [--pipe PIPE] [file|-]
  tir-pukiwiki --version

Options:
  --pipe PIPE   Replacement for '|' in table cells during unparse (default: '｜')

If file is omitted or '-', parse reads from stdin.
If file is omitted or '-', unparse writes to stdout.
""",
        file=sys.stderr,
    )


def parse_args(argv):
    pipe = "｜"
    remaining_args = []

    argument_iterator = iter(argv)

    for argument in argument_iterator:
        if argument == "--pipe":
            try:
                pipe = next(argument_iterator)
            except StopIteration:
                raise ValueError("--pipe requires an argument")
        else:
            remaining_args.append(argument)

    return pipe, remaining_args


# ------------------------------------------------------------
# entry
# ------------------------------------------------------------


def run(argv) -> int:
    global pipe
    try:
        pipe, args = parse_args(argv)
    except Exception as error:
        print(str(error), file=sys.stderr)
        usage()
        return 1

    if not args:
        usage()
        return 1

    if args[0] == "--version":
        print(get_version())
        return 0

    if len(args) not in (1, 2):
        usage()
        return 1

    command = args[0]
    file_argument = args[1] if len(args) == 2 else None

    try:
        if command == "parse":
            parse(file_argument)
        elif command == "unparse":
            unparse(file_argument)
        else:
            print(f"unknown sub command: {command}", file=sys.stderr)
            usage()
            return 1

    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1

    return 0
