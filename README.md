# Metadata-Historical-Land-Registry-Basel
This repository contains Python scripts for processing metadata of the Historical Land Registry of the City of Basel.

## Requirements
- Python 3.10 or newer (only on Python 3.10 tested)
- Packages: see requirements.txt

## Notes
- These scripts were developed as part of the following research project: https://dg.philhist.unibas.ch/de/bereiche/mittelalter/forschung/oekonomien-des-raums/
- Metadata from Linked Open Data of the Basel State Archives are processed. Source: https://ld.staatsarchiv.bs.ch/
- More information about the historical land register can be found in German at https://www.staatsarchiv.bs.ch/benutzung/recherche/suche-gedruckte-kataloge/historisches-grundbuch.html.

## queryMetadata.py
This script contains functions to query metadata of the "Historische Grundbuch Basel (HGB)" from the Staatsarchiv. Additional functions allow to extract attributes of interest for the entities "Serie" and "Dossier" as used in our research project. The SPARQL endpoint of the Staatarchiv can be accessed at https://ld.staatsarchiv.bs.ch/sparql/.

## Contact
For questions please contact jonas.aeby@unibas.ch.