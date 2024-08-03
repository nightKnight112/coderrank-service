#!/bin/bash

query=$1

cat << EOF > input.sql
BEGIN;
${query}
ROLLBACK;
EOF

sudo docker exec -i pgcontainer psql -U postgres -d postgres < input.sql > output.log