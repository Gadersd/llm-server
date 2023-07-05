#!/bin/bash

# Find the file location
FILE_LOCATION=$(find / -name libcudart.so 2>/dev/null)

# If the file was found, add it to the LD_LIBRARY_PATH
if [ -n "$FILE_LOCATION" ]; then
  LIB_PATH=${FILE_LOCATION%/*}
  echo "Found path: $LIB_PATH"

  # Check if the path is already in .bashrc
  if ! grep -q "LD_LIBRARY_PATH=.*$LIB_PATH" ~/.bashrc; then
    echo "Updating .bashrc with the found path..."
    echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:$LIB_PATH" >> ~/.bashrc
    echo ".bashrc updated. Please restart your terminal or run 'source ~/.bashrc'"
  else
    echo "The path is already in .bashrc"
  fi
else
  echo "File libcudart.so not found."
fi
