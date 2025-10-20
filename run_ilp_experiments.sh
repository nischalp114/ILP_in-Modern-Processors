#!/usr/bin/env bash
set -euo pipefail

GEM5="/Users/nischalpokharel/gem5/build/X86/gem5.opt"
CONF="$HOME/ilp_assignment/se_run_x86.py"
BIN="/Users/nischalpokharel/gem5/tests/test-progs/hello/bin/x86/linux/hello"
OUTDIR="$HOME/ilp_assignment/runs"

mkdir -p "$OUTDIR"

run () {
  local label="$1"; shift
  echo "=== Running $label ==="
  "$GEM5" --outdir="$OUTDIR/$label" "$CONF" --cmd="$BIN" "$@"
}

# Baseline: TournamentBP, width=1
run baseline_tournament_w1 --bp=TournamentBP --width=1 --smt=1

# Branch predictor sweep @ width=2
for BP in LocalBP TournamentBP LTAGE TAGE_SC_L; do
  run "bp_${BP}_w2" --bp="$BP" --width=2 --smt=1 || true
done

# Superscalar widths (TournamentBP)
for W in 2 4; do
  run "superscalar_w${W}" --bp=TournamentBP --width="$W" --smt=1
done

# SMT = 2 (Tournament, width=2)
run smt2_tournament_w2 --bp=TournamentBP --width=2 --smt=2
