#!/usr/bin/env bash
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and the most recent chat that
# operated in it. Emits a table sorted by size with a suggested bucket. Never
# deletes anything; deletion stays a human-gated step in the playbook.
#
# Usage: worktree-audit.sh [repo-path]   (defaults to the current repo)
set -u

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

# Main worktree is the first entry; everything else is a candidate.
main_wt=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')
{{#codex}}
workspace_roots=$(git worktree list --porcelain | awk '/^worktree /{print $2}' | jq -Rsc 'split("\n") | map(select(length > 0))')
{{/codex}}

# origin/main drives the merge check. Best-effort; stale is fine for a first pass.
git fetch origin main --quiet 2>/dev/null || echo "warn: could not fetch origin/main; merged column may be stale" >&2

# PR state by branch, fetched once. Empty if gh is unavailable.
prs=$(mktemp)
gh pr list --author "@me" --state all --limit 1000 \
	--json number,state,headRefName 2>/dev/null > "$prs" || echo "[]" > "$prs"

{{#claude}}
# Claude stores each workspace under its own project key. Search only the
# project dirs belonging to the listed worktrees, including the main worktree.
transcript_dirs=$(
	git worktree list --porcelain | awk '/^worktree /{print $2}' |
	while read -r worktree; do
		slug=$(printf '%s' "$worktree" | sed 's/[^[:alnum:]]/-/g')
		printf '%s\n' "$HOME/.claude/projects/$slug"
	done
)
{{/claude}}
{{#codex}}
# Codex rollout files: ${CODEX_HOME:-$HOME/.codex}/sessions/YYYY/MM/DD/rollout-*.jsonl.
rollouts="${CODEX_HOME:-$HOME/.codex}/sessions"
{{/codex}}
now=$(date +%s)

printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE\n"

git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do
	[ "$wt" = "$main_wt" ] && continue

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of main, so PR state is the
	# real signal; merge-base only catches fast-forward/rebase merges.
	git merge-base --is-ancestor "$head" origin/main 2>/dev/null && merged=YES || merged=no

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	porcelain=$(git -C "$wt" status --porcelain 2>/dev/null)
	if [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		[ "$(git -C "$wt" rev-parse "origin/$branch" 2>/dev/null)" = "$head" ] \
			&& remote=pushed \
			|| remote="ahead$(git -C "$wt" rev-list --count "origin/$branch..HEAD" 2>/dev/null)"
	else remote=no-remote; fi

	pr=$([ -n "$branch" ] && jq -r --arg b "$branch" \
		'.[] | select(.headRefName==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
	[ -z "$pr" ] && pr="-"

{{#claude}}
	# Most recent chat whose transcript operated in this worktree. Match path
	# followed by "/" or a quote so glint-482 does not match glint-482-r37.
{{/claude}}
{{#codex}}
	# Most recent visible Codex session that operated in this worktree.
	# Exclude reasoning/encrypted records; only response items can establish use.
{{/codex}}
	last="-"; last_ts=0
{{#claude}}
	while IFS= read -r transcripts; do
		[ -d "$transcripts" ] || continue
		while IFS= read -r f; do
			[ -n "$f" ] || continue
			file_ts=$(stat -f '%m' "$f" 2>/dev/null || echo 0)
			if [ "$file_ts" -gt "$last_ts" ]; then
				last_ts=$file_ts
{{/claude}}
{{#codex}}
	if [ -d "$rollouts" ]; then
		while IFS= read -r -d '' f; do
			# Read only the session metadata first. A rollout belongs to this
			# repository when its cwd is a listed worktree or a descendant.
			if ! jq -e --argjson roots "$workspace_roots" '
				select(.type == "session_meta")
				| .payload.cwd as $cwd
				| select(($roots | any(.[]; . as $root | $cwd == $root or ($cwd | startswith($root + "/")))) )
				| true
			' "$f" >/dev/null 2>&1; then
				continue
{{/codex}}
			fi
{{#claude}}
		done < <(rg -l --glob '*.jsonl' -e "${wt}/" -e "${wt}\"" "$transcripts" 2>/dev/null || true)
	done <<< "$transcript_dirs"
	if [ "$last_ts" -gt 0 ]; then
		last=$(date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null)
{{/claude}}
{{#codex}}
			# select(...)|true keeps jq successful when any visible record matches,
			# even if later rollout records do not.
			if jq -e --arg path "$wt" '
				select(
					.type == "response_item"
					and (.payload.type == "message"
						or .payload.type == "agent_message"
						or .payload.type == "custom_tool_call"
						or .payload.type == "function_call")
				and ((.payload | del(.. | .encrypted_content?) | tojson)
					| (contains($path + "/") or contains($path + "\"")))
				)
				| true
			' "$f" >/dev/null 2>&1; then
				ts=$(stat -f '%m' "$f" 2>/dev/null || echo 0)
				if [ "$ts" -gt "$last_ts" ] 2>/dev/null; then last_ts=$ts; last=$f; fi
			fi
		done < <(find "$rollouts" -type f -name 'rollout-*.jsonl' -print0 2>/dev/null)
		if [ "$last_ts" -gt 0 ] 2>/dev/null; then last=$(date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null); fi
{{/codex}}
	fi
	recent=$([ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	case "$dirty" in wip:*) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=safe
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh

rm -f "$prs"
