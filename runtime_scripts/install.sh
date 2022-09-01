#!/bin/bash

PACKAGE_DIR=$1

echo "installing component packages"
python3.10 -m pip install --upgrade --target $PACKAGE_DIR -r $PACKAGE_DIR/component/requirements.txt
