#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/remote_ops_lib.sh
source "${SCRIPT_DIR}/remote_ops_lib.sh"

DRY_RUN=0
PRUNE_TOP_LEVEL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --prune-top-level)
      PRUNE_TOP_LEVEL=1
      shift
      ;;
    *)
      printf '[remote-cleanup] unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

require_remote_ops_cmds
ensure_remote_password

cleanup_snippet="$(render_remote_cleanup_snippet)"
targets_array="$(render_remote_targets_array)"
keep_array="$(render_remote_keep_array)"
prune_snippet="$(render_remote_prune_top_level_snippet)"

if (( DRY_RUN == 1 )); then
  remote_log "dry-run remote cleanup under ${REMOTE_PROJECT_ROOT}"
  remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
${targets_array}
${keep_array}
echo '[remote-cleanup] would remove AppleDouble and cache files under' \"\$PWD\"
find . -name '._*' | sort
find . -name '.DS_Store' | sort
find . -name '__pycache__' -type d | sort
if [ -d .pytest_cache ]; then echo .pytest_cache; fi
if [ -d .ruff_cache ]; then echo .ruff_cache; fi
if [ -d frontend/tmp ]; then echo frontend/tmp; fi
find \"\$(dirname \"\$PWD\")\" -maxdepth 1 -name '._*' | sort
if (( ${PRUNE_TOP_LEVEL} == 1 )); then
  echo '[remote-cleanup] would prune unexpected top-level entries under' \"\$PWD\"
  shopt -s dotglob nullglob
  allowed_entries=(\"\${targets[@]}\" \"\${keep_entries[@]}\")
  for entry in * .*; do
    name=\"\$(basename \"\$entry\")\"
    case \"\$name\" in
      .|..)
        continue
        ;;
    esac
    keep=0
    for allowed in \"\${allowed_entries[@]}\"; do
      if [[ \"\$name\" == \"\$allowed\" ]]; then
        keep=1
        break
      fi
    done
    if (( keep == 0 )); then
      printf '%s\n' \"\$name\"
    fi
  done | sort
  shopt -u dotglob nullglob
fi
"
  exit 0
fi

remote_log "cleaning remote garbage under ${REMOTE_PROJECT_ROOT}"
remote_container_bash "
set -euo pipefail
cd $(printf '%q' "$REMOTE_PROJECT_ROOT")
${cleanup_snippet}
if (( ${PRUNE_TOP_LEVEL} == 1 )); then
  ${targets_array}
  ${keep_array}
  ${prune_snippet}
fi
"

remote_log "remote cleanup finished"
