#!/bin/bash

curl --request POST \
  --url http://localhost:8065/api/v4/posts \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer z7zh999da3n4pdbmcwk66bfqio' \
  --header 'Content-Type: application/json' \
  --data '{
  "channel_id": "wp7j9cdmapf5fn7a97byqahcme",
  "message": "dummy"
}'
