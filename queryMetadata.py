"""Script to query the metadata of the 'Historische Grundbuch Basel'.

This module provides specific functions for querying metadata, which is made
available in the Linked Open Data Portal of the State Archives Basel-Stadt.
"""


from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import re
import logging
import requests


def query_series():
    """Query all series of interest of the "Historisches Grundbuch Basel".
    Args:
        None.

    Returns:
        list: Metadata of series from the HGB1.
    """
    sparql = SPARQLWrapper("https://ld.bs.ch/query/")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rico: <https://www.ica.org/standards/RiC/ontology#>
        SELECT ?link ?identifier ?title
        WHERE {
            {
            ?link rico:identifier ?identifier ;
            rico:title ?title ;
            rico:type "Akte"@ger ;
            rico:isDirectlyIncludedIn <https://ld.bs.ch/ais/Record/1027330> .
            }
        }
        """
                    )
    ret = sparql.queryAndConvert()

    # Store the data as transformed list.
    series_list = []
    for r in ret["results"]["bindings"]:
        serie = {}
        for key, val in r.items():
            serie[key] = val["value"]
        series_list.append(serie)
    return series_list


def get_series(series_data):
    """Extract the series attributes of interest and store them in a dataframe.
    Args:
        series_data (list): List of series metadata created by query_series().

    Returns:
        DataFrame: Table of series metadata.
    """
    df_series = pd.DataFrame(columns=['stabsId', 'title', 'link'])
    for serie in series_data:
        df_serie = pd.DataFrame({'stabsId': [serie['identifier']],
                                 'title': [serie['title']],
                                 'link': [serie['link']]}
                                )
        df_series = pd.concat([df_series, df_serie], ignore_index=True)
    return df_series


def get_serie_id(identifier):
    """Based on the identifier of the serie, create the project id.
    Args:
        identifier (list): List of series metadata created by query_series().

    Returns:
        DataFrame: Table of series metadata.
    """
    identifier = identifier.split(" ")
    identifier = f"HGB_{identifier[1]}_{int(identifier[2]):03}"
    return identifier


def query_dossiers(link_serie):
    """Given a serie URI, all connected dossier where queried.
    Args:
        link_serie (str): URI of a serie.

    Returns:
        list or None: Metadata of connected dossiers.
    """
    sparql = SPARQLWrapper("https://ld.bs.ch/query/")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rico: <https://www.ica.org/standards/RiC/ontology#>
        PREFIX stabs-rico:
            <https://ld.bs.ch/ontologies/StABS-RiC/>
        SELECT ?link ?identifier ?title ?note ?housenamebs ?oldhousenumber
            ?owner1862
            WHERE {{
                    {{
                    ?link rico:identifier ?identifier ;
                    rico:title ?title ;
                    rico:type "Akte"@ger ;
                    rico:isDirectlyIncludedIn <{}> .
                    }}
                OPTIONAL {{?link rico:generalDescription ?note .}}
                OPTIONAL {{?link stabs-rico:houseNameBS ?housenamebs .}}
                OPTIONAL {{?link stabs-rico:oldHousenumber ?oldhousenumber .}}
                OPTIONAL {{?link stabs-rico:owner1862 ?owner1862 .}}
            }}
            """.format(link_serie)
                    )
    ret = sparql.queryAndConvert()

    if not ret["results"]["bindings"]:
        logging.warning('For the following serie, no dossier was found: '
                        f'{link_serie}.'
                        )
        return None
    else:
        # Store the data as transformed list.
        dossiers = []
        for r in ret["results"]["bindings"]:
            dossier = {}
            for key, val in r.items():
                dossier[key] = val["value"]
            dossiers.append(dossier)
        return dossiers


def get_dossiers(link_serie):
    """ Get all relevant dossier information.
    Given a serie URI, all information of interest from the connected dossiers
    where queried.

    Args:
        link_serie (str): URI of a serie.

    Returns:
        DataFrame or None: Metadata of connected dossiers.
    """
    dossiers = query_dossiers(link_serie)
    if dossiers:
        df_dossiers = pd.DataFrame(
            columns=['stabsId', 'title', 'houseName', 'oldHousenumber',
                     'owner1862', 'descriptiveNote', 'link']
                     )
        for dossier in dossiers:
            df_dossier = pd.DataFrame(
                {'stabsId': [dossier.get('identifier')],
                 'title': [dossier.get('title')],
                 'houseName': [dossier.get('housenamebs')],
                 'oldHousenumber': [dossier.get('oldhousenumber')],
                 'owner1862': [dossier.get('owner1862')],
                 'descriptiveNote': [dossier.get('note')],
                 'link': [dossier.get('link')]
                 })
            df_dossiers = pd.concat([df_dossiers, df_dossier],
                                    ignore_index=True
                                    )
        return df_dossiers
    else:
        return None


def get_dossier_id(identifier):
    """ Based on the identifier of the dossier, create the project id.
    Args:
        identifier (str): Identifier of the dossier.

    Returns:
        str: Project id of the dossier.
    """
    identifier_split = re.split(r'\s+|/', identifier)
    id = f'HGB_{identifier_split[1]}_{int(identifier_split[2]):03}_'\
        f'{int(identifier_split[3]):03}'
    return id


def query_documents(link_serie):
    """Given a serie URI, all connected documents where queried.
    The query parameters of this function is optimized to query all documents
    of the serie "Regesten Klingental", see record
    https://ld.bs.ch/ais/Record/751516.

    Args:
        link_serie (str): URI of a serie.

    Returns:
        list or None: Metadata of connected documents.
    """
    sparql = SPARQLWrapper("https://ld.bs.ch/query/")
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
        PREFIX rico: <https://www.ica.org/standards/RiC/ontology#>
        SELECT ?link ?identifier ?title ?type ?descriptivenote
            ?isassociatedwithdate
            WHERE {{
                    {{
                    ?link rico:identifier ?identifier ;
                    rico:title ?title ;
                    rico:type ?type ;
                    rico:isIncludedInTransitive <{}> .
                    }}
                OPTIONAL {{?link rico:generalDescription ?descriptivenote .}}
                OPTIONAL {{?link rico:isAssociatedWithDate
                    ?isassociatedwithdate .}}
            }}
            """.format(link_serie)
                    )
    ret = sparql.queryAndConvert()

    if not ret["results"]["bindings"]:
        logging.warning('For the following serie, no dossier was found: '
                        f'{link_serie}.'
                        )
        return None
    else:
        # Store the data as transformed list.
        dossiers = []
        for r in ret["results"]["bindings"]:
            dossier = {}
            for key, val in r.items():
                dossier[key] = val["value"]
            dossiers.append(dossier)
        return dossiers


def get_date(link_date):
    """Given the URI of a associated date, the expressed date is returned.
    Args:
        link_serie (str): URI of a associated date record.

    Returns:
        str or None: Associated date (if available).
    """
    r = requests.get(link_date + '?format=jsonld')
    if r.status_code == requests.codes.ok:
        return r.json()[
            'https://www.ica.org/standards/RiC/ontology#expressedDate'
            ]
    else:
        logging.warning('No associated date record found for '
                        f'{link_date}. Return: {r.text} ({r}).'
                        )
        return None
