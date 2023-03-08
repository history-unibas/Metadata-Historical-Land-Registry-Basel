#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Enriches the metadata of the 'Historische Grundbuch Basel' from the Staatsarchiv
by creating additional attributes.
"""


import pandas as pd
import numpy as np
import re
from datetime import datetime
from ast import literal_eval


def get_new_house_number(dossier_title):
    # Given a dossier title, returns the extracted house number
    
    # Exclude titles containing ":" that are usually are no addresses, for example "Kanonengasse: Übersicht" 
    address_match = re.search(r":", dossier_title)
    if address_match:
        return None

    # Search simple adress pattern with housenumber at the end, for example "St. Johanns-Vorstadt 2"
    address_match = re.match(r"[A-Za-zäöü.\-\s]+[0-9]+[a-z]?$", dossier_title)
    if address_match:
        address = address_match.group()
        address_split = address.split(' ')
        # Case if no whitespace is existing, e.g. "Malzgasse10"
        if len(address_split) == 1:
            house_number = re.search(r"[0-9]+[a-z]?$", address)
            return house_number.group()
        return address_split[-1]
    
    # Search first appearance of a number, for example "St. Johanns-Vorstadt 8, 10". Else, return None.
    house_number = re.search(r"[0-9]+[a-z]?", dossier_title)
    if house_number:
        return house_number.group()
    else:
        return None


def split_old_house_number(old_house_number, new_house_number):
    """Given an old house number as string, returns a pandas series with the following values:
    - oldHousenumberNumber: guess of the old house number
    - oldHousenumberSupplement: supplement of the given old house number
    - oldHousenumberNeighbouringNumber: guess of the house number of the neighbour
    - oldHousenumberIsPartOf: guess if entry is part of a house number
    - oldHousenumberIsBann: True if string "Bann" or "bann" is part of oldHousenumber
    """
    
    if pd.isna(old_house_number):
        return pd.Series([None, None, None, None, None])

    is_bann = False

    while True:
        # Detect old house humbers from "Bann"
        bann_match = re.search(r"(Bann)|(bann)", old_house_number)
        if bann_match:
            is_bann = True

        # Search simple numbers like "1257" and "1257 A" as well as multiple simple numbers
        # like "1052, 1053, 1054", "1097 / 1096", "827 + 827 A", "1250 u. 1251"
        number_match = re.match(r"^([0-9]+\s?[a-zA-Z]?(,\s|\s/\s|\s\+\s|\su\.\s)?)+$", old_house_number)
        if number_match:
            number_split = re.split(r",\s|\s/\s|\s\+\s|\su\.\s", old_house_number)
            result = pd.Series([number_split, None, None, False, is_bann])
            break
        
        # Search for numbers with postfix " (Bann)", for example "48 A (Bann)"
        number_match = re.match(r"^([0-9]+\s?[a-zA-Z]?(,\s|\s/\s)?)+\s\(Bann\)$", old_house_number)
        if number_match:
            number_split = re.split(r",\s|\s/\s|\s\(Bann\)", old_house_number)
            result = pd.Series([number_split[:-1], None, None, False, is_bann])
            break
    
        # Search for numbers with arbitrary postfix, for example "441 A u. Th. v. 440 neben 441 A"
        number_match = re.match(r"^[0-9]+\s?[a-zA-Z]?.+$", old_house_number)
        if number_match:
            number = re.search(r"^[0-9]+\s?([a-zA-Z](\s|,))?", old_house_number).group()
            supplement = old_house_number[len(number):]
            if re.search(r",$|\s$", number):
                number = number[:-1]
            result = pd.Series([[number], supplement, None, False, is_bann])
            break
        
        # Search for numbers with prefix "Th. v.", "Theil von", "Theil v." or "Th. von" without any postfix,
        # for example "Theil von 744 A neben 745", "Theil von 126, 124"
        number_match = re.match(
            r"^(Th. v.|Theil von|Theil v.|Th. von)\s([0-9]+\s?[a-zA-Z]?(,\s)*)+(\sneben)?\s?[0-9]*\s?[a-zA-Z]?$",
            old_house_number)
        if number_match:
            number_split = re.split(r"Th. v.\s|Theil von\s|Theil v.\s|Th. von\s|\sneben\s|,\s", old_house_number)
            if re.search(r"neben", old_house_number):
                number = [number_split[1]]
                supplement = 'neben'
                neighbouring_number = number_split[-1]
            else:
                number = number_split[1:]
                supplement = None
                neighbouring_number = None
            result = pd.Series([number, supplement, neighbouring_number, True, is_bann])
            break
        
        # Search for numbers with prefix "Th. v.", "Theil von", "Theil v." or "Th. von" and arbitrary postfix,
        # for example "Theil von 1084, zweites Haus von 1085", "Theil von 552, 551, Vorderhaus"
        number_match = re.match(r"^(Th. v.|Theil von|Theil v.|Th. von)\s[0-9]+\s?[a-zA-Z]?.+$", old_house_number)
        if number_match:
            number_split = re.split(r"Th. v.\s|Theil von\s|Theil v.\s|Th. von\s|,\s|\s", old_house_number)

            # Detect house number postfixes, for example "Theil von 1045 A und B"
            if len(number_split[2]) == 1 and number_split[2].isalpha():
                number = [number_split[1] + " " + number_split[2]]
                supplement_start = re.search(number_split[3], old_house_number).start()
                supplement = old_house_number[supplement_start:]

            # Detect multiple house numbers, for example "Theil von 552, 551, Hinterhaus"
            elif number_split[2].isnumeric():
                number = []
                index = None
                for index in range(1, len(number_split)):
                    if number_split[index].isnumeric():
                        number.append(number_split[index])
                    else:
                        break
                supplement_start = re.search(number_split[index], old_house_number).start()
                supplement = old_house_number[supplement_start:]

            else:
                number_split = re.split(r"Th. v.\s|Theil von\s|Theil v.\s|Th. von\s|,\s|\s", old_house_number, maxsplit=2)
                number = [number_split[1]]
                supplement = number_split[2]

            # Search for neighbouring number
            neighbouring_number = None
            neighbouring_match = re.search(r"^(Th. v.|Theil von|Theil v.|Th. von)\s[0-9]+\s?[a-zA-Z]?\sneben\s[0-9]+",
                                           old_house_number)
            if neighbouring_match:
                neighbouring_split = re.split(r"\s", neighbouring_match.group())
                neighbouring_number = neighbouring_split[-1]

            result =  pd.Series([number, supplement, neighbouring_number, True, is_bann])
            break

        return pd.Series([None, None, None, None, is_bann])
    
    # Test if detected old house number is new house number
    if new_house_number in result[0]:
        return pd.Series([None, 'Log: Alte Hausnummer wurde als neue Hausnummer detektiert. Alte Hausnummer wurde nicht aufbereitet.', None, None, None])
    else:
        return result


def get_first_entry(my_list):
    try:
        return my_list[0]
    except:
        return None


def correct_old_house_number(dossierid, oldhousenumber_number, oldhousenumber_ispartof,
                             oldhousenumber_neighbouringnumber, oldhousenumber_supplement,
                             df_corrections):
    '''Correct additional oldHousenumber attributes. The following attributes are edited/created:
    - oldHousenumberNumber (replaced)
    - oldHousenumberIsPartOf (replaced)
    - oldHousenumberNeighbouringNumber (replaced)
    - oldHousenumberSupplement (complemented)
    - oldHousenumberIsCorrected (new created)
    '''
    
    # Check if dossierId do not exist in correction dataframe
    if dossierid not in df_corrections['dossierId'].tolist():
        return pd.Series([oldhousenumber_number, oldhousenumber_ispartof, oldhousenumber_neighbouringnumber, oldhousenumber_supplement, False])

    dossierid_corrections = df_corrections[df_corrections['dossierId']==dossierid]

    # Replace oldHousenumberNumber if corrected value exist
    if pd.notnull(dossierid_corrections['oldHouseNumberNumberCorr']).any():
        oldhousenumber_number = literal_eval(dossierid_corrections['oldHouseNumberNumberCorr'].iloc[0])

    # Replace oldHousenumberIsPartOfCorr if corrected value exist
    if pd.notnull(dossierid_corrections['oldHousenumberIsPartOfCorr']).any():
        oldhousenumber_ispartof = dossierid_corrections['oldHousenumberIsPartOfCorr'].iloc[0]

    # Replace oldHousenumberNeighbouringNumber if corrected value exist
    if pd.notnull(dossierid_corrections['oldHousenumberNeighbouringNumberCorr']).any():
        oldhousenumber_neighbouringnumber = dossierid_corrections['oldHousenumberNeighbouringNumberCorr'].iloc[0]

    # Complement oldHousenumberSupplement if corrected value exist
    if pd.notnull(dossierid_corrections['oldHousenumberSupplementAddition']).any():
        if pd.isna(oldhousenumber_supplement):
            oldhousenumber_supplement = 'manuell erfasste Bemerkung: ' + dossierid_corrections['oldHousenumberSupplementAddition'].iloc[0]
        else:
            oldhousenumber_supplement += ' , zusätzliche manuell erfasste Bemerkung: ' + dossierid_corrections['oldHousenumberSupplementAddition'].iloc[0]

    return pd.Series([oldhousenumber_number, oldhousenumber_ispartof, oldhousenumber_neighbouringnumber, oldhousenumber_supplement, True])


if __name__ == "__main__":
    # Read series and dossiers created by https://github.com/history-unibas/Postgresql-Project-Database/blob/main/updateProjectDatabase.py
    series_data = pd.read_csv('data/stabs_serie.csv')
    all_dossiers = pd.read_csv('data/stabs_dossier.csv')

    # Identify first new house number based on the title of the dossier
    all_dossiers['housenumberFromTitle'] = all_dossiers.apply(lambda row: get_new_house_number(row['title']), axis=1)

    # Create additional attributes based on the old house number and check for new house numbers
    all_dossiers[['oldHousenumberNumber',
                  'oldHousenumberSupplement',
                  'oldHousenumberNeighbouringNumber',
                  'oldHousenumberIsPartOf',
                  'oldHousenumberIsBann']] = all_dossiers.apply(
        lambda row: split_old_house_number(row['oldHousenumber'], row['housenumberFromTitle']), axis=1)
    
    # Correct additional oldHousenumber attributes based on the manually created file oldHousenumberCorrections.csv
    corrections = pd.read_csv('oldHousenumberCorrections.csv')

    all_dossiers[['oldHousenumberNumber',
                  'oldHousenumberIsPartOf',
                  'oldHousenumberNeighbouringNumber',
                  'oldHousenumberSupplement',
                  'oldHousenumberIsCorrected']] = all_dossiers.apply(
        lambda row: correct_old_house_number(dossierid=row['dossierId'],
                                             oldhousenumber_number=row['oldHousenumberNumber'],
                                             oldhousenumber_ispartof=row['oldHousenumberIsPartOf'],
                                             oldhousenumber_neighbouringnumber=row['oldHousenumberNeighbouringNumber'],
                                             oldhousenumber_supplement=row['oldHousenumberSupplement'],
                                             df_corrections=corrections),
                                             axis=1)

    # Create a new attribut storing the first extracted old house number
    all_dossiers['oldHousenumberNumberFirst'] = all_dossiers.apply(
        lambda row: get_first_entry(row['oldHousenumberNumber']), axis=1)

    # Join the series to the dossier
    dossiers_serie = pd.merge(all_dossiers, series_data, how='left', on='serieId', suffixes=('', '_serie'),
                              validate='many_to_one')

    # Write the data created
    today = datetime.today()
    dossiers_serie.to_csv("data/" + today.strftime("%Y%m%d") + "_hgb_metadaten.csv", index=False, header=True)
    dossiers_serie.to_json("data/" + today.strftime("%Y%m%d") + "_hgb_metadaten.json", orient='records', lines=True)
