#!/bin/sh

# This script calls each end-to-end scenario sequentially and verifies the
# result

# Exit on error
set -e

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"

$DIR/e2e-scenario-1.sh
$DIR/e2e-scenario-1-verify.sh
$DIR/e2e-scenario-2.sh
$DIR/e2e-scenario-2-verify.sh
$DIR/e2e-scenario-3.sh
$DIR/e2e-scenario-3-verify.sh
