#!/bin/bash

set -euo pipefail

ROOT="/Users/bishmaybarik/Library/CloudStorage/Dropbox/suspicious-co"

CLAUDE_WT="$HOME/.agent-worktrees/suspicious-co/claude"
CODEX_WT="$HOME/.agent-worktrees/suspicious-co/codex"

INPUT_DIR="$HOME/.agent-inputs/suspicious-co"

CLAUDE_BRANCH="agent/claude"
CODEX_BRANCH="agent/codex"

PROMPT_FILE="$ROOT/orchestration/prompts/autonomous_cycle.md"

ROUNDS="${1:-3}"

RUN_ID="$(date '+%Y%m%d_%H%M%S')"
LOG_DIR="$ROOT/orchestration/logs/$RUN_ID"

mkdir -p "$LOG_DIR"

echo "============================================"
echo "Suspicious-Co Dual-Agent Research"
echo "Run ID: $RUN_ID"
echo "Rounds: $ROUNDS"
echo "============================================"
echo


run_claude () {

    ROUND="$1"

    echo
    echo "============================================"
    echo "ROUND $ROUND — CLAUDE OPUS 5"
    echo "============================================"

    git -C "$CLAUDE_WT" fetch origin --prune

    OTHER_SHA="$(
        git -C "$CLAUDE_WT" rev-parse "origin/$CODEX_BRANCH"
    )"

    PROMPT="$(
        cat <<PROMPT_HEADER
This is autonomous collaboration cycle $ROUND.

You are Claude Opus 5.

The other research agent is Codex / GPT-5.6 Sol.

Other agent remote branch:

origin/$CODEX_BRANCH

Latest available Codex commit:

$OTHER_SHA

PROMPT_HEADER

        cat "$PROMPT_FILE"
    )"

    mkdir -p "$CLAUDE_WT/.agent_runtime"

    (
        cd "$CLAUDE_WT"

        claude -p "$PROMPT" \
          --model claude-opus-5 \
          --permission-mode dontAsk \
          --add-dir "$INPUT_DIR" \
          --max-turns 100 \
          --output-format text \
          --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python *),Bash(python3 *),Bash(stata *),Bash(stata-mp *),Bash(pdflatex *),Bash(latexmk *),Bash(make *),Bash(mkdir *),Bash(git status *),Bash(git log *),Bash(git show *),Bash(git diff *),Bash(git rev-parse *),Bash(git branch *)" \
          --disallowedTools "Bash(git commit *),Bash(git push *),Bash(git merge *),Bash(git rebase *),Bash(git reset *),Bash(git clean *),Bash(git checkout *),Bash(git switch *)"
    ) 2>&1 | tee "$LOG_DIR/round_${ROUND}_claude.log"

    echo
    echo "Committing Claude's research increment..."

    "$ROOT/orchestration/commit_agent.sh" claude

    echo
    echo "Claude round $ROUND pushed successfully."
}


run_codex () {

    ROUND="$1"

    echo
    echo "============================================"
    echo "ROUND $ROUND — CODEX / GPT-5.6 SOL"
    echo "============================================"

    #
    # This fetch is crucial:
    # Codex now sees the Claude commit produced just above.
    #
    git -C "$CODEX_WT" fetch origin --prune

    OTHER_SHA="$(
        git -C "$CODEX_WT" rev-parse "origin/$CLAUDE_BRANCH"
    )"

    PROMPT="$(
        cat <<PROMPT_HEADER
This is autonomous collaboration cycle $ROUND.

You are Codex using GPT-5.6 Sol.

The other research agent is Claude Opus 5.

Other agent remote branch:

origin/$CLAUDE_BRANCH

Latest available Claude commit:

$OTHER_SHA

PROMPT_HEADER

        cat "$PROMPT_FILE"
    )"

    mkdir -p "$CODEX_WT/.agent_runtime"

    (
        cd "$CODEX_WT"

        codex \
          -a never \
          exec \
          -m gpt-5.6-sol \
          -s workspace-write \
          -c 'model_reasoning_effort="max"' \
          "$PROMPT"
    ) 2>&1 | tee "$LOG_DIR/round_${ROUND}_codex.log"

    echo
    echo "Committing Codex's research increment..."

    "$ROOT/orchestration/commit_agent.sh" codex

    echo
    echo "Codex round $ROUND pushed successfully."
}


for ROUND in $(seq 1 "$ROUNDS")
do

    echo
    echo
    echo "############################################"
    echo "# COLLABORATION ROUND $ROUND / $ROUNDS"
    echo "############################################"
    echo

    #
    # Claude first reviews everything Codex has produced so far,
    # then produces new work.
    #
    run_claude "$ROUND"

    #
    # Codex immediately sees Claude's newly pushed commit.
    #
    run_codex "$ROUND"

    #
    # Refresh Claude's view so the next round starts with
    # Codex's latest contribution available.
    #
    git -C "$CLAUDE_WT" fetch origin --prune

done


echo
echo
echo "============================================"
echo "AUTOMATED RESEARCH BATCH COMPLETE"
echo "============================================"
echo

echo "Latest Claude commit:"
git -C "$CLAUDE_WT" log -1 --oneline

echo
echo "Latest Codex commit:"
git -C "$CODEX_WT" log -1 --oneline

echo
echo "Logs saved to:"
echo "$LOG_DIR"
