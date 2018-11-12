#!/usr/bin/env bash

whoami

# Setup ssh first
# Should setup env var first with GIT_USERNAME and GIT_EMAIL
eval $(ssh-agent -s)
ssh-add /secrets/ssh-privatekey
ssh-add -l
git config --global user.name "${GIT_USERNAME}"
git config --global user.email "${GIT_EMAIL}"

# Add known hosts
mkdir -p ~/.ssh
echo "github.com,192.30.253.112 ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==" >> ~/.ssh/known_hosts
echo "[gitlab.cern.ch]:7999,[188.185.68.18]:7999 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBBswtRsTLbTluK4lN2gk71Wp020NxNZcihjhUfUoJ7+hrHamzX5wjZBjwEBtgyzISYrstd1giRrP5qfqIf+dUyY=" >> ~/.ssh/known_hosts

# Test command
git fetch origin

# The following bit is as per the run script
# https://github.com/sclorg/s2i-python-container/blob/master/3.6/s2i/bin/run

# Guess the number of workers according to the number of cores
function get_default_web_concurrency() {
  limit_vars=$(cgroup-limits)
  local $limit_vars
  if [ -z "${NUMBER_OF_CORES:-}" ]; then
    echo 1
    return
  fi

  local max=$((NUMBER_OF_CORES*2))
  # Require at least 43 MiB and additional 40 MiB for every worker
  local default=$(((${MEMORY_LIMIT_IN_BYTES:-MAX_MEMORY_LIMIT_IN_BYTES}/1024/1024 - 43) / 40))
  default=$((default > max ? max : default))
  default=$((default < 1 ? 1 : default))
  # According to http://docs.gunicorn.org/en/stable/design.html#how-many-workers,
  # 12 workers should be enough to handle hundreds or thousands requests per second
  default=$((default > 12 ? 12 : default))
  echo $default
}

# Run the server
export WEB_CONCURRENCY=${WEB_CONCURRENCY:-$(get_default_web_concurrency)}
exec gunicorn wsgi --bind=0.0.0.0:8080 --access-logfile=- --config "$APP_CONFIG"
