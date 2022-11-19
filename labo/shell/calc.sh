#!/bin/bash

# 足し算
i=0
while [ $i -lt 10 ]; do
    i=$((i+1))
    echo $i

    if [ $i == 5 ]; then
        break
    fi
done

# 掛け算
i=$(( (1+5)*10 ))
echo $i
