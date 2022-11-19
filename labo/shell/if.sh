#!/bin/bash


# コマンド実行結果における条件分岐
if echo "hogepiyo" | grep "hoge"; then
    echo "grep hoge"
fi

if echo "hogepiyo" | grep "foo"; then
    echo "grep foo"
fi


# true, falseにおける条件分岐
true1=true
false1=false

if "$true1"; then
    echo "true"
fi

if "$false1"; then
    echo "false"
fi

if [ "$true1" = true -a "$false1" = true ]; then
    echo "true and false"
fi

if [ "$true1" = true -o "$false1" = true ]; then
    echo "true or false"
fi

if [ "$false" = true -o "$false1" = true ]; then
    echo "true or false"
fi
