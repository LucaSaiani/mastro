#!/bin/bash

for f in *.svg; do
	inkscape "$f" --export-type=png --export-width=256 --export-filename="${f%.svg}.png"
done 

mv -f *.png png/

echo "Conversion done"
