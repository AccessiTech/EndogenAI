#!/usr/bin/env bash
# build_images.sh — Build all EndogenAI Docker images in dependency order.
#
# Usage:
#   bash scripts/build_images.sh              # build all images
#   bash scripts/build_images.sh --push       # build and push to registry
#   bash scripts/build_images.sh --skip-base  # skip base image builds
#
# Environment:
#   IMAGE_TAG  — image tag (default: latest)
#
set -eu

PUSH=""
SKIP_BASE=""
for arg in "$@"; do
  case "$arg" in --push) PUSH=1 ;; --skip-base) SKIP_BASE=1 ;; esac
done

TAG="${IMAGE_TAG:-latest}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

function build_and_push() {
  local IMAGE="$1" DOCKERFILE="$2" CONTEXT="${3:-.}"
  echo "Building: $IMAGE ..."
  docker build -t "endogenai/$IMAGE:$TAG" -f "$DOCKERFILE" "$CONTEXT"
  if [[ -n "$PUSH" ]]; then
    docker push "endogenai/$IMAGE:$TAG"
  fi
}

# 1. Base images
if [[ -z "$SKIP_BASE" ]]; then
  build_and_push "base-python" "deploy/docker/base-python.Dockerfile"
  build_and_push "base-node" "deploy/docker/base-node.Dockerfile"
fi

# 2. Group I — Signal Processing
build_and_push "sensory-input" "modules/group-i-signal-processing/sensory-input/Dockerfile"
build_and_push "perception" "modules/group-i-signal-processing/perception/Dockerfile"
build_and_push "attention-filtering" "modules/group-i-signal-processing/attention-filtering/Dockerfile"

# 3. Group II — Cognitive Processing
build_and_push "working-memory" "modules/group-ii-cognitive-processing/memory/working-memory/Dockerfile"
build_and_push "short-term-memory" "modules/group-ii-cognitive-processing/memory/short-term-memory/Dockerfile"
build_and_push "long-term-memory" "modules/group-ii-cognitive-processing/memory/long-term-memory/Dockerfile"
build_and_push "episodic-memory" "modules/group-ii-cognitive-processing/memory/episodic-memory/Dockerfile"
build_and_push "reasoning" "modules/group-ii-cognitive-processing/reasoning/Dockerfile"
build_and_push "affective" "modules/group-ii-cognitive-processing/affective/Dockerfile"

# 4. Group III — Executive Output
build_and_push "executive-agent" "modules/group-iii-executive-output/executive-agent/Dockerfile"
build_and_push "agent-runtime" "modules/group-iii-executive-output/agent-runtime/Dockerfile"
build_and_push "motor-output" "modules/group-iii-executive-output/motor-output/Dockerfile"

# 5. Group IV — Adaptive Systems
build_and_push "learning-adaptation" "modules/group-iv-adaptive-systems/learning-adaptation/Dockerfile"
build_and_push "metacognition" "modules/group-iv-adaptive-systems/metacognition/Dockerfile"

# 6. Infrastructure
build_and_push "mcp-server" "infrastructure/mcp/Dockerfile"

# 7. Apps
build_and_push "gateway" "apps/default/server/Dockerfile" "apps/default/server"

echo "All images built successfully: $(date)"
echo "Tag: endogenai/*:$TAG"
