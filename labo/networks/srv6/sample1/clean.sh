#!/bin/bash

for ns in h1 h2 r1 r2 r3 r4; do
	ip netns del $ns
done
