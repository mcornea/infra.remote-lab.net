#!/usr/bin/env bash
curl --silent https://sai-vanguard.ro/etf-bet-tradeville | grep data.addRows | tr ';' '\n' | grep data.set | awk -F ',' {'print $3'} | sed s/\'//g | sed s/\)/\ /g | sed ':a;N;$!ba;s/\n\ //g' > /tmp/tradeville.etf
curtime=$(date +%s); sed s/^/TVBETETF./ /tmp/tradeville.etf | sed s/$/$curtime/g
