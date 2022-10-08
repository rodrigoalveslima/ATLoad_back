#!/bin/bash

# Copyright (C) 2022 Georgia Tech Center for Experimental Research in Computer
# Systems

# This script formats Python code according to the Google style standards.

# Change to the parent directory.
cd "$(dirname "$(dirname "$(readlink -fm "$0")")")"

# Process command-line arguments.
set -u
while [[ $# > 1 ]]; do
  case $1 in
    * )
      echo "Invalid argument: $1"
      exit 1
  esac
  shift
  shift
done

# Format Python files.
for filepath in $(find -type f | grep ".*\.py$")
do
  yapf -i --style='{based_on_style: google, indent_width: 2, column_limit: 160}' $filepath
done
