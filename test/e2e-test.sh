#!/bin/sh

# This script calls each end-to-end scenario sequentially and verifies the
# result

# Exit on error
set -e

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"

$DIR/e2e-scenario-1.sh
$DIR/e2e-scenario-1-verify.sh

