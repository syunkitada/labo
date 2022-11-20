#!/bin/bash

for ns in r1 h1 h2; do
	ip netns del $ns
done
