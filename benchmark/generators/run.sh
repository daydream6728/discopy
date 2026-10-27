#!/bin/bash
# Run jobs of distributions.py against a checkout, e.g. the base of #1 then
# this branch, each importing its own code:
#   OUT=out benchmark/generators/run.sh ../base samples:search bugs:search
#   OUT=out benchmark/generators/run.sh . samples:boltzmann bugs:boltzmann
#   python benchmark/generators/analyse.py out
SP="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "${OUT:-$SP/out}"; OUT="$(cd "${OUT:-$SP/out}" && pwd)"
cd "$1"; shift; export PYTHONPATH="$PWD"
for job in "$@"; do
  kind=${job%%:*}; g=${job#*:}
  timeout 5400 .venv/bin/python $SP/distributions.py $g ${OUT:-$SP/out}/$kind-$g.jsonl $kind > ${OUT:-$SP/out}/log-$kind-$g.txt 2>&1
  echo "done $job"
done
