#!/bin/bash

# Splices together LCHEAPO file segments

if [ $# -lt 3 ]
then
	echo "Usage: lcSplice.sh file1 gap1 file2 gap2 file3 .... fileN outFile"
	echo "     where gapN is the gap IN BLOCKS between the end of fileN and the "
	echo "     beginning of fileN+1"
	exit 1
fi

args=("$@")		# make array of command line arguments
outfile=${args[ $#-1 ]}
echo "outfile=$outfile"
echo "cp $1 tmp.base"
for (( i=1; i< $# -2 ; i+=2 ))
do
	echo "dd if=/dev/zero of=tmp.gap bs=512 count=${args[$i]}"
	echo "cat tmp.base tmp.gap ${args[$i+1]} > tmp.base2"
	echo "mv tmp.base2 tmp.base"
done

echo "mv tmp.base $outfile"

echo rm tmp.gap
echo rm tmp.base2
echo rm tmp.base
