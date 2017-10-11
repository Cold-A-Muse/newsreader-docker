#!/bin/bash

cat | ./nlpp
# cat | text2naf -l $NAFLANG | nlpp
# cat | text2naf -l $NAFLANG 

#java -jar ixa-pipe-tok/target/ixa-pipe-tok-1.8.5-exec.jar tok -l nl |\
#    /morphosyntactic_parser_nl/run_parser.sh |\
#    java -jar /ixa-pipe-nerc/target/ixa-pipe-nerc-1.6.1-exec.jar tag -m /models/nerc-models-1.5.4/nl/nl-6-class-clusters-sonar.bin
