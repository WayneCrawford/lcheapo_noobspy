BAD.bad.lch has tons of time tears, is from 2019 SMARTIES site SM03
BUGGY.raw.lch has normal bugs, is from 2019 SMARTIES station SM19

both were cut down from the original to 10000 blocks using the command
> dd bs=512 count=10000 if=inputfile of=outputfile

BUGGY.fix.*      were generated using ```lcfix BUGGY.raw.lch```
BAD_tt/BAD.fix.* were generated using ```lcfix -o BAD_tt BAD.bad.lch```
BAD.fix.*        were generated using ```lcfix --forceTimes BAD.bad.lch```
