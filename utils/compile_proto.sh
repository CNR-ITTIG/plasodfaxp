#!/bin/bash
# Script to compile protobufs.

compile()
{
  protoc -I=. --python_out=. plaso/proto/$1
}

compile plaso_storage.proto
