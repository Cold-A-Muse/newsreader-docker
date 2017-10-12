#!/bin/bash
# set -e
# set -o pipefail
thisdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export NAFLANG=$1
cd ${thisdir}
# cat | nlpp
cat | ./text2naf -l $NAFLANG | ./nlpp

#java -jar ixa-pipe-tok/target/ixa-pipe-tok-1.8.5-exec.jar tok -l nl |\
#    /morphosyntactic_parser_nl/run_parser.sh |\
#    java -jar /ixa-pipe-nerc/target/ixa-pipe-nerc-1.6.1-exec.jar tag -m /models/nerc-models-1.5.4/nl/nl-6-class-clusters-sonar.bin
