#!/bin/bash

pybtex-convert jsh_bib.bib jsh_bib.yaml

python yaml_pd.py --short_version False
python yaml_pd.py --short_version True

cp publications.html ../scotthosking.github.io/04_publications.html
cp publications_short.html ../scotthosking.github.io/05_publications_short.html