#!/bin/sh
set -u

tir-pukiwiki help > gen.txt 2>&1
grep -vE '^tir-pukiwiki [0-9]' gen.txt > out-actual.txt || true