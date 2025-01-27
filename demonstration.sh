#!/usr/bin/env bash

echo "demonstration.sh: Using this config file:"
echo
cat ./settings/demo.yaml

rm -rf ./datasets_out/demo

echo
echo "demonstration.sh: Running 'python3 -m vampireman --settings-file ./settings/demo.yaml'"
echo
read

python3 -m vampireman --settings-file ./settings/demo.yaml

echo
echo "demonstration.sh: Done"
echo
read

echo
echo "demonstration.sh: Contents of ./datasets_out"
echo
tree datasets_out

echo
echo "demonstration.sh: Running again"
echo
read

python3 -m vampireman --settings-file ./settings/demo.yaml

