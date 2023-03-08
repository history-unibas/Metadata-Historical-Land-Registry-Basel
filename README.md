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
This script contains functions to query metadata of the "Historische Grundbuch Basel (HGB)" from the Staatsarchiv. The SPARQL endpoint of the Staatarchiv can be accessed at https://ld.staatsarchiv.bs.ch/sparql/. Additional functions allow to extract attributes of interest for the entities "Serie" and "Dossier" as used in our research project. The functions are used in particular in the following script: https://github.com/history-unibas/Postgresql-Project-Database/blob/main/updateProjectDatabase.py.

## enrichMetadata.py
Enriches the metadata of the 'Historische Grundbuch Basel' from the Staatsarchiv by creating additional attributes. The databasis of this script was created by the function processing_metadat() within https://github.com/history-unibas/Postgresql-Project-Database/blob/main/updateProjectDatabase.py.

Additional attributes are included in the resulting dataframe 'dossiers_series'. The following table describes each of these additional attributes.

| **Column name** | **Description** |
|---------------|---------------|
| housenumberFromTitle | First number given in column "title". |
| oldHousenumberNumber* | Based on the column "oldHousenumber", the best guess of the old house numbers are stored as list. |
| oldHousenumberSupplement* | Additions in the column "oldHousenumber". |
| oldHousenumberNeighbouringNumber* | Based on the column "oldHousenumber", detected neighbouring house numbers. |
| oldHousenumberIsPartOf* | Boolean column based on "oldHousenumber". True, if old house number is part of another house. |
| oldHousenumberIsBann | Boolean column based on "oldHousenumber". True, if old house number is located in a "Bann". |
| oldHousenumberIsCorrected | Boolean column indicating if columns based on "oldHousenumber" are manuelly corrected, see "*" below for details. |
| oldHousenumberNumberFirst | Extract of the first number stored in the column "oldHousenumberNumber". |

(*) For those columns, a few values are manually corrected based on the file "oldHousenumberCorrections.csv". If a corresponding value in the correction file exist, the values are replaced for oldHousenumberNumber, oldHousenumberIsPartOf and oldHousenumberNeighbouringNumber. For the column oldHousenumberSupplement, additional remarks from the correction file are added. The manual correction is based on the following principle:

| **Pattern** | **Solution** |
|---------------|---------------|
| Old house number: "Teil von XY und YZ" (possibly whole parcel) | YZ (as a whole parcel) mentioned first and isPartOf set to False, remark that "Zusätzlich Teil von XY" (but only if unambiguous!): "Zusätzlich Teil von (zu prüfen)"; other cases with remark "Zusätzlich Teil von", but this is probably not fully documented (and also not so important). |
| Old house number: XY-YZ | Hyphen not interpreted as from-to, but only house numbers actually mentioned noted, as misleading. |
| from XY | Seems to be a phenomenon of the 19th century, to be read as part of house number XY. Transposed without further comment. |

## Contact
For questions please contact jonas.aeby@unibas.ch.