#!/bin/sh

DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1; pwd -P )"

$DIR/e2e-scenario-1.sh
$DIR/e2e-scenario-1-verify.sh

