#!/bin/sh
# Test that newline and tab characters are correctly converted to \n and \t
# When a file name is specified, the absolute path of the file is output
set -eu
exec > out-actual.txt 2>&1

tir-pukiwiki parse "$TIRENVI_ROOT/tests/data/sample.pukiwiki" | tir-pukiwiki unparse