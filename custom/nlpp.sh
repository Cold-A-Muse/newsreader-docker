#!/bin/bash
# testit -- test newly installed pipeline
# 20170907 Paul Huygen
export thisdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
oldd=`pwd`
bindir=${thisdir}
export confdir=/usr/local/etc/nlpp
progname=$0
unset keep_temp
unset workdir

function show_help () {
echo "usage: $progname [-k] [-t workdir ] < infile > outfile"
echo "infile : raw naf"
echo "outfile : annotated naf"
echo "-k : Keep intermediate results in the workdir"
echo "-t : use workdir for intermediate results"
}

while getopts "h?vkt:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    v)  verbose=1
        ;;
    k)  keep_temp=0
        ;;
    t)  workdir=$OPTARG
    esac
done

initscript=${confdir}/conf
source $initscript
if
    [ -z ${workdir+x} ]
then
    workdir=`mktemp -d -t nlpp.XXXXXX`
fi
res=0

function runmodule {
   local infile=$1
   local modnam=$2
   local outfile=$3
   cat ${infile} | $MODROOT/${modnam}/run > ${outfile}
   res=$?
}


# run_pipeline -- run the pipeline
# Assume current dir is work-dir, contains in.naf.
function run_pipeline () {
    
    nohup java -Xms2500m -cp /usr/local/share/pipelines/nlpp/nlppmodules/ixa-pipe-srl/IXA-EHU-srl/target/IXA-EHU-srl-3.0.jar ixa.srl.SRLServer en >&2
    naflang=$1
    modulelist=${confdir}/modules.${naflang}
    lastfile=in.naf
    while
	IFS=' ' read -r module || [[ -n "$module" ]]
    do
	echo "Annotate ${lastfile} with ${module}" >&2
        nextfile=${module}.naf
        cat ${lastfile} | ${MODROOT}/${module}/run >${module}.naf
	res=$?
	if
	    [ ${res} -gt 0 ]
	then
	    echo "Module ${module} failed." >&2
	    break
	fi
	lastfile=${module}.naf
    done < ${modulelist}
    ln -s ${lastfile} out.naf
}

cd $workdir
cat >in.naf
export naflang=`cat in.naf | $bindir/langdetect.py`
if
    [ "$naflang" != "nl" -a "$naflang" != "en" ]
then
    echo "Language $naflang is not supported." >&2
    exit 4
fi
res=0
run_pipeline $naflang
cd $oldd
if
    [ $res -gt 0 ]
then
    echo "Pipeline has not been completed due to an error." >&2
    exit 4
fi
cat ${workdir}/out.naf
if
    [ -z ${keep_temp+x} ]
then
    rm -rf $workdir
else
    echo "$workdir kept" >&2
fi
