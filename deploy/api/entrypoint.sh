#!/bin/sh
set -eu

load_secret() {
  variable_name="$1"
  secret_path="$2"
  if [ ! -r "$secret_path" ]; then
    echo "Required secret file is unavailable: $secret_path" >&2
    exit 1
  fi
  secret_value="$(cat "$secret_path")"
  if [ -z "$secret_value" ]; then
    echo "Required secret file is empty: $secret_path" >&2
    exit 1
  fi
  export "$variable_name=$secret_value"
}

load_secret DATABASE_URL /run/secrets/database_url
load_secret RATE_LIMIT_BACKEND_URL /run/secrets/rate_limit_backend_url

exec "$@"
