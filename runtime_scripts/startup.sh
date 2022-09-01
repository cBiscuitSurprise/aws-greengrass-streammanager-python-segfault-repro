#!/bin/bash

PACKAGE_DIR=$1

echo "launching component"
cd $PACKAGE_DIR
python3.10 -m component
