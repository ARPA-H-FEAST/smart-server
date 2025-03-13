#!/bin/bash

pushd ../datadir/releases/current/tarballs 2>&1 > /dev/null

for filename in *.txt; do
    echo Tarballing $filename
    tarname=$(echo $filename | sed -e 's/txt/tar.gz/g')
    echo Running command tar -czf $tarname $filename
    tar -czf $tarname $filename
done

popd 2>&1 > /dev/null