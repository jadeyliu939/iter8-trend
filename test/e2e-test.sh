#!/usr/bin/env bash

# This script calls each end-to-end scenario sequentially and verifies the
# result

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"

# install yq
which yq
if (( $? )); then
  sudo apt-get update
  sudo apt-get install software-properties-common
  sudo add-apt-repository -y ppa:rmescandon/yq
  sudo apt update
  sudo apt install yq -y
fi

# Exit on error
set -e

$DIR/../iter8/test/e2e/e2e-canary-scenario-1.sh
$DIR/../iter8/test/e2e/e2e-canary-scenario-2.sh
#$DIR/e2e-scenario-0a-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-0b.sh
#$DIR/e2e-scenario-0b-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-0c.sh
#$DIR/../iter8/test/e2e/e2e-scenario-1.sh
#$DIR/e2e-scenario-1-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-2.sh
#$DIR/e2e-scenario-2-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-3.sh
#$DIR/e2e-scenario-3-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-4.sh
#$DIR/e2e-scenario-4-verify.sh
#$DIR/../iter8/test/e2e/e2e-scenario-5.sh
#$DIR/e2e-scenario-5-verify.sh
