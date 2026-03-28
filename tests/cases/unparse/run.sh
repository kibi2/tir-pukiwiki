#!/bin/sh
set -eu
exec > out-actual.txt 2>&1

tir-pukiwiki unparse < "$TIRENVI_ROOT/tests/data/complex.tir"
