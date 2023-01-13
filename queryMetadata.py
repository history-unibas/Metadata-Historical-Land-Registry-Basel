#!/usr/bin/env python3


"""
Script to query the metadata of the 'Historische Grundbuch Basel' from the Staatsarchiv.

SPARQL endpoint of Staatsarchiv Basel
https://ld.staatsarchiv.bs.ch/sparql/
"""


from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import warnings
import re


def query_series():
    # Query all Series of interest of the "Historisches Grundbuch Basel"
    sparql = SPARQLWrapper("https://ld.staatsarchiv.bs.ch/query/")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
            PREFIX rico: <https://www.ica.org/standards/RiC/ontology#>
            SELECT ?link ?identifier ?title
            WHERE {
                {
                ?link rico:identifier ?identifier ;
                rico:title ?title ;
                rico:type "Akte"@ger ;
                rico:isOrWasIncludedIn <https://ld.staatsarchiv.bs.ch/Record/1027330> .
                }
            }
            """
                    )
    ret = sparql.queryAndConvert()

    # Store the data as transformed list
    series_list = []
    for r in ret["results"]["bindings"]:
        serie = {}
        for key, val in r.items():
            serie[key] = val["value"]
        series_list.append(serie)
    return series_list


def get_series(series_data):
    # Extract the series attributes of interest and store them in a dataframe
    df_series = pd.DataFrame(columns=['stabsId', 'title', 'link'])
    for serie in series_data:
        df_serie = pd.DataFrame({'stabsId': [serie['identifier']], 'title': [serie['title']], 'link': [serie['link']]})
        df_series = pd.concat([df_series, df_serie], ignore_index=True)
    return df_series


def get_serie_id(identifier):
    # Based on the identifier of the serie, create the project id
    identifier = identifier.split(" ")
    identifier = f"HGB_{identifier[1]}_{int(identifier[2]):03}"
    return identifier


def query_dossiers(link_serie):
    # Given a serie url, all dossiers where queried
    sparql = SPARQLWrapper("https://ld.staatsarchiv.bs.ch/query/")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rico: <https://www.ica.org/standards/RiC/ontology#>
        SELECT ?link ?identifier ?title ?note ?housenamebs ?oldhousenumber ?owner1862
            WHERE {{
                    {{
                    ?link rico:identifier ?identifier ;
                    rico:title ?title ;
                    rico:type "Akte"@ger ;
                    rico:isOrWasIncludedIn <{}> .
                    }}
                OPTIONAL {{?link rico:descriptiveNote ?note .}}
                OPTIONAL {{?link <https://ld.staatsarchiv.bs.ch/ontologies/StABS-RiC/houseNameBS> ?housenamebs .}}
                OPTIONAL {{?link <https://ld.staatsarchiv.bs.ch/ontologies/StABS-RiC/oldHousenumber> ?oldhousenumber .}}
                OPTIONAL {{?link <https://ld.staatsarchiv.bs.ch/ontologies/StABS-RiC/owner1862> ?owner1862 .}}
            }}
            """.format(link_serie)
                    )
    ret = sparql.queryAndConvert()

    if not ret["results"]["bindings"]:
        warnings.warn("For the following serie, no dossier was found: " + link_serie)
        return None
    else:
        # Store the data as transformed list
        dossiers = []
        for r in ret["results"]["bindings"]:
            dossier = {}
            for key, val in r.items():
                dossier[key] = val["value"]
            dossiers.append(dossier)
        return dossiers


def get_dossiers(link_serie):
    # Given a serie url, the function queries all corresponding dossier information as dataframe
    dossiers = query_dossiers(link_serie)
    if dossiers:
        df_dossiers = pd.DataFrame(columns=['stabsId', 'title', 'houseName', 'oldHousenumber', 'owner1862',
                                            'descriptiveNote', 'link'])
        for dossier in dossiers:
            df_dossier = pd.DataFrame({'stabsId': [dossier.get('identifier')],
                                       'title': [dossier.get('title')],
                                       'houseName': [dossier.get('housenamebs')],
                                       'oldHousenumber': [dossier.get('oldhousenumber')],
                                       'owner1862': [dossier.get('owner1862')],
                                       'descriptiveNote': [dossier.get('note')],
                                       'link': [dossier.get('link')]
                                       })
            df_dossiers = pd.concat([df_dossiers, df_dossier], ignore_index=True)
        return df_dossiers
    else:
        return None


def get_dossier_id(identifier):
    # Based on the identifier of the dossier, create the project id
    identifier = re.split(" |\/", identifier)
    identifier = f"HGB_{identifier[1]}_{int(identifier[2]):03}_{int(identifier[3]):03}"
    return identifier


if __name__ == "__main__":
    # Query all series
    print('Query series...')
    series_data = query_series()

    # Extract attributes of interest
    series_data = get_series(series_data)

    # Generate the "project_id" of the series
    series_data['serieId'] = series_data.apply(lambda row: get_serie_id(row['stabsId']), axis=1)

    # Get all dossiers from all series
    all_dossiers = pd.DataFrame(columns=['dossierId', 'title', 'houseName', 'oldHousenumber', 'owner1862',
                                         'descriptiveNote', 'link'])
    for index, row in series_data.iterrows():
        print('Query dossier', row['link'], '...')
        dossiers = get_dossiers(row['link'])

        # If serie does not have any dossier
        if not isinstance(dossiers, pd.DataFrame):
            continue
        else:
            # Add series_id to dossiers
            dossiers['serieId'] = row['serieId']

            all_dossiers = pd.concat([all_dossiers, dossiers], ignore_index=True)

    # Generate the "project_id" of the dossiers
    all_dossiers['dossierId'] = all_dossiers.apply(lambda row: get_dossier_id(row['stabsId']), axis=1)

    # Write the data created
    series_data.to_csv("series.csv", index=False, header=True)
    all_dossiers.to_csv("dossiers.csv", index=False, header=True)
