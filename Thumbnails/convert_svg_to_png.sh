#!/bin/bash

shopt -s nullglob

if [ $# -eq 0 ]; then
    files=( *.svg )
else
    files=()
    for pattern in "$@"; do
        [[ "$pattern" != *.svg ]] && pattern="${pattern}.svg"
        IFS=$'\n' matches=( $(compgen -G "$pattern") )
        for match in "${matches[@]}"; do
            files+=( "$match" )
        done
    done
fi

mkdir -p png

for f in "${files[@]}"; do
    if [[ -f "$f" ]]; then
        output="png/${f%.svg}.png"
        inkscape "$f" --export-type=png --export-width=256 --export-filename="$output"
        echo "Convertito: $f → $output"
    else
        echo "File non trovato: $f"
    fi
done

echo "Conversione completata"

