#!/bin/bash
set -euo pipefail

AGENT="${1:?Usage: commit_agent.sh claude|codex}"

case "$AGENT" in

  claude)
    WT="$HOME/.agent-worktrees/suspicious-co/claude"
    BRANCH="agent/claude"
    TRAILER="Co-authored-by: Claude Opus 5 <noreply@anthropic.com>"
    FALLBACK="research(claude): complete exploratory research increment"
    ;;

  codex)
    WT="$HOME/.agent-worktrees/suspicious-co/codex"
    BRANCH="agent/codex"
    TRAILER="Co-authored-by: Codex (GPT-5.6 Sol) <codex@openai.com>"
    FALLBACK="research(codex): complete exploratory research increment"
    ;;

  *)
    echo "Unknown agent: $AGENT"
    exit 1
    ;;
esac

MSGFILE="$WT/.agent_runtime/commit_message.txt"

if [[ -z "$(git -C "$WT" status --porcelain)" ]]; then
  echo "No changes from $AGENT."
  exit 0
fi

if [[ -s "$MSGFILE" ]]; then
  SUBJECT="$(head -n 1 "$MSGFILE")"
else
  SUBJECT="$FALLBACK"
fi

git -C "$WT" add -A

TMPMSG="$(mktemp)"

{
  echo "$SUBJECT"
  echo
  echo "$TRAILER"
} > "$TMPMSG"

git -C "$WT" commit -F "$TMPMSG"

rm -f "$TMPMSG"

git -C "$WT" push -u origin "$BRANCH"

echo
echo "Committed and pushed:"
git -C "$WT" show --stat --oneline --decorate HEAD
