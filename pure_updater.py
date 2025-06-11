import os, sys
import requests
import json
import csv
import math
import datetime
import pandas as pd
from IPython.display import clear_output

from pure_classif.json_keyw_oa_class import *
from pure_classif.json_keyw_oa_colour import *
from pure_classif.json_keyw_lw_class import *
from pure_classif.json_keyw_ys_class import *
from pure_classif.json_ev_access_status import *
from pure_classif.json_ev_version import *
from pure_classif.json_cc_licenses import *

from config import PURE_BASE_URL, PURE_524_API_KEY, PURE_CRUD_API_KEY, SCOPUS_API_KEY

from get_pure_record import getPure, get_pure
from get_crossref_record import getCrossref
from get_scopus_record import getScopus
from get_openalex_record import getOpenalex
from get_doaj_record import getDOAJ
from get_pure_persons.get_pure_internal_persons import get_pure_internal_persons

from create_pure_record import create_ext_org, create_ext_person

def analyze_scopus_contrib(scopus_record, int_person_df, pure_record):
    
    # Check Scopus person and org IDs against Pure to determine if internal/external
    # Return contrib list / df external persons / df external orgs / df missing persons
    
    #dataframes
    df_external_orgs = pd.DataFrame(columns=['org-id', 'org-name', 'org-country'])
    df_external_persons = pd.DataFrame(columns=['au-id', 'au-surnm', 'au-fname', 'af-ids'])
    df_missing_persons = pd.DataFrame(columns=['au-id', 'au-surnm', 'au-fname', 'af-ids'])
    df_intern_person_no_auid = pd.DataFrame(columns=['publ uuid', 'title', 'sub-title', 'managing org', 'person uuid', 'scopus AU-ID'])

    contrib_list = []
    print ('analyzing scopus contrib section')
    for author in scopus_record.contrib:
        au_fname = author['auth_first_name']
        au_lname = author['auth_last_name']
        person_affil = []
        
        #Match Scopus au-id with Pure internal person records df - partial string match to include Scopus AI-IDs labeled as 'false'
        pure_match = int_person_df.loc[int_person_df['scopus_ids'].str.contains(author['auth_id'], na=False)]
        if not pure_match.empty:
            for row_label, row in pure_match.iterrows():
                #check exact match scopus au-id
                if row['scopus_ids'] == author['auth_id']:
                    #label as internal author
                    origin = 'internal'
                    au_id = row['person_uuid']
                else:
                    #inexact match: label as external author
                    au_id = author['auth_id']
                    origin = 'external'

        #No matching scopus AU-ID in Pure-persons       
        else:
            #if author has VU-affil in Scopus - keep as internal
            for affil in author['auth_affil']:
                if affil['affil_id'] in vu_af_ids:        
                    origin = 'internal'
                    au_id = row['person_uuid']
                    df_intern_person_no_auid.loc[len(df_intern_person_no_auid.index)] = [pure_record.uuid, pure_record.main_title, pure_record.sub_title, pure_record.managing_org, au_id, author['auth_id']]
                    break
                
                else:
                    #To prevent internal author becoming external if Scopus ID is missing from person record - match on last name Scopus vs Pure publ record
                    match_count = 0
                    for contributor in pure_record.contributors:
                        if contributor['typeDiscriminator'] == "InternalContributorAssociation":
                            if contributor['name']['lastName'].lower() == au_lname.lower():
                                match_count += 1
                                au_id = contributor['person']['uuid']
                                origin = 'internal'    
                        else:
                            continue
                    #in case of 0 or 1+ last name matches: label as external author anyway - if there is 1 match, first check if internal person does have scopus AU-ID - if not keep matched person in record
                    if match_count != 1:
                        au_id = author['auth_id']
                        origin = 'external'
                    else:
                        #check if matched author record in Pure does have any scopus AU-ID
                        match_uuid = int_person_df.loc[int_person_df['person_uuid'] == au_id]
                        for row_label, row in match_uuid.iterrows():
                            if pd.isna (row['scopus_ids']) == False:
                                au_id = author['auth_id']
                                origin = 'external'
                            else:
                                #keep internal person as matched above and add row to df for authors listed on a publ without scopus AU-ID in Pure (should be checked if correctly related to publ)
                                df_intern_person_no_auid.loc[len(df_intern_person_no_auid.index)] = [pure_record.uuid, pure_record.main_title, pure_record.sub_title, pure_record.managing_org, au_id, author['auth_id']] 
                
        # Create author affiliations
        
        # External author
        if origin == 'external':
            if author['auth_affil'] != []:
                #determine if author should be hidden - in this case only when an author collaboration is present and all authors do have an affiliation (mixed_affil is False)
                if scopus_record.mixed_affil == False and scopus_record.collab != []:
                    auth_hidden = True
                else:
                    auth_hidden = False
                #loop through scopus author affiliations
                for affil in author['auth_affil']:
                    if affil['affil_id'] not in person_affil:
                        person_affil.append(affil['affil_id'])

                        #Check if Scopus af-id belongs to VU
                        if affil['affil_id'] in vu_af_ids:
                            #external person with VU-affiliation, so add to missing persons df
                            df_missing_persons.loc[len(df_missing_persons.index)] = [author['auth_id'], author['auth_last_name'], author['auth_first_name'], person_affil]
                            #add scopus af-id to external org df
                            check = df_external_orgs.loc[df_external_orgs['org-id'] == affil['affil_id']]
                            if check.empty:
                                df_external_orgs.loc[len(df_external_orgs.index)] = [affil['affil_id'], affil['org_name'], affil['org_country']]
                            else:
                                continue
                        else:
                            #add scopus af-id to external org df
                            check = df_external_orgs.loc[df_external_orgs['org-id'] == affil['affil_id']]
                            if check.empty:
                                df_external_orgs.loc[len(df_external_orgs.index)] = [affil['affil_id'], affil['org_name'], affil['org_country']]
                            else:
                                continue
                    else:
                        continue
            else:
                #no affiliations in Scopus record
                #determine if author should be hidden - in this case always when an author collaboration is present
                if scopus_record.collab != []:
                    auth_hidden = True
                else:
                    auth_hidden = False
                                 
            df_external_persons.loc[len(df_external_persons.index)] = [author['auth_id'], author['auth_last_name'], author['auth_first_name'], person_affil]

        #Internal author
        if origin == 'internal':
            if author['auth_affil'] != []:
                #determine if author should be hidden - in this case only when an author collaboration is present and all authors do have an affiliation (mixed_affil is False)
                if scopus_record.mixed_affil == False and scopus_record.collab != []:
                    auth_hidden = True
                else:
                    auth_hidden = False
                #loop through scopus author affiliations
                for affil in author['auth_affil']:
                    if affil['affil_id'] not in person_affil:
                        # VU affiliations
                        if affil['affil_id'] in vu_af_ids:
                            yr_diff = 1000
                            affil_ct = 0
                            most_recent = None

                            # Get pure affils from Pure person df
                            pure_affil_match = int_person_df.loc[int_person_df['scopus_ids'] == author['auth_id'], 'personaffiliations']

                            # Select pure affil based on pub year
                            for pure_affils in pure_affil_match:
                                for affil in pure_affils:
                                    # Pub yr within affil -> add
                                    if affil['af_start'].year <= int(scopus_record.pub_year) <= affil['af_end'].year:
                                        if affil['af_org_id'] not in person_affil:
                                            person_affil.append(affil['af_org_id'])
                                            affil_ct += 1
                                    # Evaluate as most recent
                                    else:
                                        yr_diff_affil = int(scopus_record.pub_year) - affil['af_end'].year
                                        if yr_diff_affil < yr_diff and yr_diff_affil > 0:
                                            yr_diff = yr_diff_affil
                                            most_recent = affil['af_org_id']

                            # Add most recent past affil
                            if affil_ct == 0 and most_recent is not None:
                                person_affil.append(most_recent)
                            # Before VU-affil so add VU as external org
                            elif affil_ct == 0 and most_recent is None:
                                person_affil.append('60008734')
                                df_external_orgs.loc[len(df_external_orgs.index)] = ['60008734', '', '']
                            else:
                                continue
                            
                        # Add external affil
                        else:
                            person_affil.append(affil['affil_id'])
                            check = df_external_orgs.loc[df_external_orgs['org-id'] == affil['affil_id']]                    
                            if check.empty:
                                df_external_orgs.loc[len(df_external_orgs.index)] = [affil['affil_id'], affil['org_name'], affil['org_country']]
                            else:
                                continue
                    else:
                        continue
            else:
                #no affiliations in Scopus record
                #determine if author should be hidden - in this case always when an author collaboration is present
                if scopus_record.collab != []:
                    auth_hidden = True
                else:
                    auth_hidden = False
                    
                #set internal affiliations
                yr_diff = 1000
                affil_ct = 0
                most_recent = None

                # Get pure affils from Pure person df
                pure_affil_match = int_person_df.loc[int_person_df['scopus_ids'] == author['auth_id'], 'personaffiliations']

                # Select pure affil based on pub year
                for pure_affils in pure_affil_match:
                    for affil in pure_affils:
                        # Pub yr within affil -> add
                        if affil['af_start'].year <= int(scopus_record.pub_year) <= affil['af_end'].year:
                            if affil['af_org_id'] not in person_affil:
                                person_affil.append(affil['af_org_id'])
                                affil_ct += 1
                        # Evaluate as most recent
                        else:
                            yr_diff_affil = int(scopus_record.pub_year) - affil['af_end'].year
                            if yr_diff_affil < yr_diff and yr_diff_affil > 0:
                                yr_diff = yr_diff_affil
                                most_recent = affil['af_org_id']

                # Add most recent past affil
                if affil_ct == 0 and most_recent is not None:
                    person_affil.append(most_recent)
                # Before VU-affil so add VU as external org
                elif affil_ct == 0 and most_recent is None:
                    person_affil.append('60008734')

                
        contrib_list.append({'au-id': au_id,'origin': origin,'au-fname': au_fname,'au-lname': au_lname, 'au-corresp': author['auth_is_corresp'], 'au-affil': person_affil, 'au-hidden': auth_hidden})
    
    return contrib_list, df_external_orgs, df_external_persons, df_missing_persons, df_intern_person_no_auid

def create_scopus_contrib(pure_record, scopus_contrib, scopus_ext_org_df, scopus_ext_person_df):
    
    #dataframe
    df_intern_person_removed = pd.DataFrame(columns=['publ uuid', 'title', 'sub-title', 'managing org', 'person uuid', 'person lname', 'person fname', 'scopus lname', 'scopus fname', 'scopus AU-ID', 'has VU-affil'])
    
    #dicts to relate scopus ids to pure uuids
    person_id_scopus2pure ={}
    org_id_scopus2pure = {}

    print ('creating new contrib section')
    
    #loop through scopus ext org and check if they exist in pure - if not create - get uuid-pure
    print ('check if ext organisations exist')
    for index_no in scopus_ext_org_df.index[0:]:
        #check if ext org exists in Pure
        print (index_no, ' of ', len(scopus_ext_org_df.index))
        data = json.dumps ({"searchString": scopus_ext_org_df['org-id'][index_no]})
        response_ext_org = requests.post(PURE_BASE_URL+'/ws/api/external-organizations/search', data = data, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        if response_ext_org.json()['count'] == 0:
            print ('create external org record')
            new_ext_org = create_ext_org(scopus_ext_org_df['org-id'][index_no], scopus_ext_org_df['org-name'][index_no], scopus_ext_org_df['org-country'][index_no])
            uuid_ext_org = new_ext_org
        else:
            uuid_ext_org = response_ext_org.json()['items'][0]['uuid']
    
        #add scopus2pure org-ids
        org_id_scopus2pure[scopus_ext_org_df['org-id'][index_no]] = uuid_ext_org
             
    #loop through scopus ext persons and check if they exist in pure - if not create - get uuid-pure
    print ('check if ext persons exist')
    for index_no in scopus_ext_person_df.index[0:]:
        #check if ext org exists in Pure
        print (index_no, ' of ', len(scopus_ext_person_df.index))
        data = json.dumps ({"searchString": scopus_ext_person_df['au-id'][index_no]})
        response_ext_pers = requests.post(PURE_BASE_URL+'/ws/api/external-persons/search', data = data, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        
        if response_ext_pers.json()['count'] == 0:
            print ('create external person record')
            new_ext_pers = create_ext_person(scopus_ext_person_df['au-id'][index_no], scopus_ext_person_df['au-surnm'][index_no], scopus_ext_person_df['au-fname'][index_no])
            uuid_ext_pers = new_ext_pers
            
        else:
            uuid_ext_pers = response_ext_pers.json()['items'][0]['uuid']
        #add scopus2pure person-ids
        person_id_scopus2pure[scopus_ext_person_df['au-id'][index_no]] = uuid_ext_pers

    #check if author collaboration in current Pure contributor section
    collab_list = []
    for contributor in pure_record.contributors:
        if contributor['typeDiscriminator'] == "AuthorCollaborationContributorAssociation":
            collab_list.append(contributor)
        else:
            continue
    
    #build new contributor + organization section for pure, based on scopus-contribution
    contributor_list = []
    int_organization_list = []
    ext_organization_list = []
    int_org_list_json = []
    ext_org_list_json = []
    int_person_list = []

    print('building new contributor section')
    for n, contributor in enumerate(scopus_contrib):
        
        #print ('author ', n, 'of', len(scopus_contrib))
        #create list of internal and/or external affiliations
        internal_affil = []
        external_affil = []
        ext_affil_list = []

        if collab_list != []:
            hidden = contributor['au-hidden']
        else:
            hidden = False
        
        if contributor['au-affil'] != []:
            for org_id in contributor['au-affil']:
                if len(org_id) == 36:
                    internal_affil.append({"systemName": "Organization", "uuid": org_id})
                    if org_id not in int_organization_list:
                        int_organization_list.append(org_id)
                        int_org_list_json.append({"systemName": "Organization", "uuid": org_id})
                else:
                    if org_id_scopus2pure[org_id] not in ext_affil_list:
                        ext_affil_list.append(org_id_scopus2pure[org_id])
                        external_affil.append({"systemName": "ExternalOrganization", "uuid": org_id_scopus2pure[org_id]})
                        if org_id_scopus2pure[org_id] not in ext_organization_list:
                            ext_organization_list.append(org_id_scopus2pure[org_id])
                            ext_org_list_json.append({"systemName": "ExternalOrganization", "uuid": org_id_scopus2pure[org_id]})

        #create json contributor
        if contributor['origin'] == "external":
            contributor_list.append({
              "typeDiscriminator": "ExternalContributorAssociation",
              "externalOrganizations": external_affil,
              "hidden": hidden,
              "correspondingAuthor": contributor['au-corresp'],
              "name": {
                "firstName": contributor['au-fname'],
                "lastName": contributor['au-lname']
              },
              "role": {
                "uri": "/dk/atira/pure/researchoutput/roles/contributiontojournal/author",
                "term": {
                  "en_GB": "Author"
                }
              },
              "externalPerson": {
                "systemName": "ExternalPerson",
                "uuid": person_id_scopus2pure[contributor['au-id']]
              }
            })
        else:
            int_person_list.append(contributor['au-id'])
            contributor_list.append({
              "typeDiscriminator": "InternalContributorAssociation",
              "externalOrganizations": external_affil,
              "hidden": hidden,
              "correspondingAuthor": contributor['au-corresp'],
              "name": {
                "firstName": contributor['au-fname'],
                "lastName": contributor['au-lname']
              },
              "role": {
                "uri": "/dk/atira/pure/researchoutput/roles/contributiontojournal/author",
                "term": {
                  "en_GB": "Author"
                }
              },
              "person": {
                "systemName": "Person",
                "uuid": contributor['au-id']
              },
              "organizations": internal_affil
            })

    if collab_list != []:
        for collab in collab_list:
            contributor_list.append(collab)
    
    contrib_upd = json.dumps({"contributors": contributor_list, "organizations": int_org_list_json, "externalOrganizations": ext_org_list_json}, indent=4)
             
    #check which current internal persons are removed in new contributor section
    for contributor in pure_record.contributors:
        if contributor['typeDiscriminator'] == "InternalContributorAssociation":
            if contributor['person']['uuid'] not in int_person_list:
                print ('removed internal person', contributor['person']['uuid'], contributor['name']['firstName'], contributor['name']['lastName'])
                for author in scopus_contrib:
                    print ('scopus: ', author['au-lname'].lower(), 'pure: ', contributor['name']['lastName'].lower())
                    if author['au-lname'].lower() == contributor['name']['lastName'].lower():
                        matched_sc_auth_auid = author['au-id']
                        matched_sc_auth_lname = author['au-lname']
                        matched_sc_auth_fname = author['au-fname']
                        if set(vu_af_ids) & set(author['au-affil']) != set():
                            has_vu_affil = True
                        else:
                            has_vu_affil = False
                        
                    else:
                        matched_sc_auth_auid = matched_sc_auth_lname = matched_sc_auth_fname = has_vu_affil = None
                #add removed pure person to df
                df_intern_person_removed.loc[len(df_intern_person_removed.index)] = [pure_record.uuid, pure_record.main_title, pure_record.sub_title, pure_record.managing_org, contributor['person']['uuid'], contributor['name']['lastName'], contributor['name']['firstName'], matched_sc_auth_lname, matched_sc_auth_fname, matched_sc_auth_auid, has_vu_affil]
                
    return contrib_upd, df_intern_person_removed

def set_publ_status_update (pure_record, crossref_record):

    #add final published date crossref if N/A in pure - TODO: add missing month / day
    pub_status_list = pure_record.json["publicationStatuses"]
    update_list = []
    fin_pub_dt = e_pub_dt = {}
    
    if pure_record.print_year == None:
        if crossref_record.print_year != None:
            fin_pub_dt['year'] = crossref_record.print_year
            if crossref_record.print_month != None:
                fin_pub_dt['month'] = crossref_record.print_month
            if crossref_record.print_day != None:
                fin_pub_dt['day'] = crossref_record.print_day
        elif crossref_record.issue_year != None:
            fin_pub_dt['year'] = crossref_record.issue_year
            if crossref_record.issue_month != None:
                fin_pub_dt['month'] = crossref_record.issue_month
            if crossref_record.issue_day != None:
                fin_pub_dt['day'] = crossref_record.issue_day
        else:
            pass
    else:
        pass

    #check if final publ status update is valid:
    if fin_pub_dt != {}:
        if pure_record.online_year != None:
            if fin_pub_dt['year'] >= pure_record.online_year:
                fin_upd_valid = 'true'
            else:
                fin_upd_valid = 'false'
        else:
            fin_upd_valid = 'true'
    else:
        fin_upd_valid = 'false'

    if fin_upd_valid == 'true':
        update_list.append('add final pub dt')
        pub_status_list.append({     
                      "publicationStatus": {
                        "uri": "/dk/atira/pure/researchoutput/status/published",
                        "term": {
                          "en_GB": "Published"
                        }
                      },
                      "publicationDate": fin_pub_dt
                    })
        
    #add online published date crossref if N/A in pure - TODO: add missing month / day
    if pure_record.online_year == None:
        if crossref_record.online_year != None:
            e_pub_dt['year'] = crossref_record.online_year
            if crossref_record.online_month != None:
                e_pub_dt['month'] = crossref_record.online_month
            if crossref_record.online_day != None:
                e_pub_dt['day'] = crossref_record.online_day
        else:
            pass
    else:
        pass

    #check if online publ status update is valid:
    if e_pub_dt != {}:
        if pure_record.print_year != None:
            if e_pub_dt['year'] <= pure_record.print_year:
                e_upd_valid = 'true'
            else:
                e_upd_valid = 'false'
        else:
            e_upd_valid = 'true'
    else:
        e_upd_valid = 'false'

    if e_upd_valid == 'true':
        update_list.append('add e-pub dt')
        pub_status_list.append({     
                      "publicationStatus": {
                        "uri": "/dk/atira/pure/researchoutput/status/epub",
                        "term": {
                          "en_GB": "E-pub ahead of print"
                        }
                      },
                      "publicationDate": e_pub_dt
                    })
    
    pub_status_upd = (json.dumps({"publicationStatuses" : pub_status_list}, indent =4))
    
    return pub_status_upd, update_list
            
def set_keyword_update (pure_record, openalex_record, doaj_record):

    update_list = []
    #determine values
    
    #set new unl_oa_status (A or B)
    if doaj_record.doaj_journ == True and pure_record.pub_yr_first >= doaj_record.doaj_start:
        unl_status = oa_a['uri']
    elif openalex_record.oa_status == ('diamond' or 'gold'):
        unl_status = oa_a['uri']
    elif openalex_record.oa_status == 'hybrid':
        unl_status = oa_b['uri']
    else:
        unl_status = None
        
    #set oa colour (TODO)

    #get index no. and value of classified keywords   
    oa_index = oa_value = lw_index = lw_value = ys_index = ys_value = oac_index = oac_value = None
    
    keyw_list = pure_record.keyw_list
    
    if oa_class['logicalName'] in pure_record.class_keyw:
        oa_unl_index = pure_record.class_keyw[oa_class['logicalName']]['index']
        oa_unl_value = pure_record.class_keyw[oa_class['logicalName']]['values'][0]
    else:
        oa_unl_index = oa_unl_value = None
    if oa_colour['logicalName'] in pure_record.class_keyw:
        oac_index = pure_record.class_keyw[oa_colour['logicalName']]['index']
        oac_value = pure_record.class_keyw[oa_colour['logicalName']]['values'][0]      
    if ys_class['logicalName'] in pure_record.class_keyw:
        ys_index = pure_record.class_keyw[ys_class['logicalName']]['index']
        ys_value = pure_record.class_keyw[ys_class['logicalName']]['values'][0]       
    if lw_class['logicalName'] in pure_record.class_keyw:
        lw_index = pure_record.class_keyw[lw_class['logicalName']]['index']
        lw_value = pure_record.class_keyw[lw_class['logicalName']]['values'][0]

    #update keywords

    #1 unl_oa_status
    
    #add when not set
    if oa_unl_value == None:
        if unl_status == oa_a['uri']: 
            oa_class['classifications'] = [oa_a]
            keyw_list.append(oa_class)
            update_list.append('add unl A')
        if unl_status == oa_b['uri']: 
            oa_class['classifications'] = [oa_b]
            keyw_list.append(oa_class)
            update_list.append('add unl B')

    #overwrite when 'unknown'
    elif oa_unl_value == [oa_unkn]:
        if unl_status == oa_a['uri']: 
            oa_class['classifications'] = [oa_a]
            keyw_list[oa_index] = oa_class
            update_list.append('add unl A')
        if unl_status == oa_b['uri']: 
            oa_class['classifications'] = [oa_b]
            keyw_list[oa_index] = oa_class
            update_list.append('add unl B')

    else: pass
    """
    #2 oa_colour - keyword classification not yet added to pure
    if oac_value != None:
        oa_colour['classifications'] = [oa_col]
        keyw_list[oac_index] = oa_colour
    else:
        oa_colour['classifications'] = [oa_col]
        keyw_list.append (oa_colour)
    """

    keyw_upd =(json.dumps({"keywordGroups" : keyw_list}, indent =4))
    
    return keyw_upd, update_list, oa_unl_value, unl_status


def set_ev_update (pure_record, openalex_record):

    ev_list = pure_record.electr_versions
    update_list = []
    
    #update DOI
    if pure_record.doi != None:
        ev_list[pure_record.doi_index]['doi'] = pure_record.doi
        if pure_record.doi_license == None or pure_record.doi_license == unspecified['uri'] and openalex_record.prim_loc_license != None:
            ev_list[pure_record.doi_index]['licenseType'] = cc_upw2pure[openalex_record.prim_loc_license]
            update_list.append('add doi-license')
        if pure_record.doi_access == ev_status_unknown['uri'] and (openalex_record.oa_status == 'diamond' or 'gold' or 'hybrid'):
            ev_list[pure_record.doi_index]['accessType'] = ev_status_open
            update_list.append('add doi-access-status')

    #check links
    has_pmc = has_link = "false"
    if pure_record.electr_versions != None:
        for ev in pure_record.electr_versions:
            if ev['typeDiscriminator'] == 'LinkElectronicVersion':
                has_link = "true"
                if "ncbi.nlm.nih.gov/pmc" in ev['link']:
                    has_pmc = "true"
                else:
                    continue
            else:
                continue

    #add links
    if has_pmc == "false" and openalex_record.pmc_loc_landing != None:
        update_list.append('add pmc-link')
        ev_list.append({
          "typeDiscriminator": "LinkElectronicVersion",
          "accessType": ev_status_open,
          "link": openalex_record.pmc_loc_landing,
          "versionType": ev_version_final})
    else:
        if has_link == "false" and openalex_record.green_url_landing != None:
            update_list.append('add repos-link')
            ev_list.append({
              "typeDiscriminator": "LinkElectronicVersion",
              "accessType": ev_status_open,
              "link": openalex_record.green_url_landing,
              "versionType": ev_version_accepted})
                   
    ev_upd =(json.dumps({"electronicVersions" : ev_list}, indent = 4))
    
    return ev_upd, update_list

def enrich_df_removed_persons (df_intern_person_removed, int_person_df):

    #add org unit names of removed person and managing org of publication to df
    df_intern_person_removed['man_org_name']=""
    df_intern_person_removed['org_pure_affil']=""
    
    for index_no in df_intern_person_removed.index[0:]:

        uuid_man_org = df_intern_person_removed['managing org'][index_no] 
        response_org = requests.get(PURE_BASE_URL+'/ws/api/organizations/'+uuid_man_org, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        df_intern_person_removed['man_org_name'][index_no] = response_org.json()['name']['en_GB']
        
        person_uuid = df_intern_person_removed['person uuid'][index_no]
        person_match = int_person_df.loc[int_person_df['person_uuid'] == person_uuid]
        person_affil = int_person_df.loc[int_person_df['person_uuid'] == person_uuid, 'personaffiliations']
        for i, item in person_affil.items():
            for affil in item:
                #if affil['af_end'] == person_match['affil_last_dt'] and affil['af_source_id'].startswith("P"):
                if affil['af_source_id'].startswith("P"):
                    response_org = requests.get(PURE_BASE_URL+'/ws/api/organizations/'+affil['af_org_id'], headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
                    df_intern_person_removed['org_pure_affil'][index_no] = response_org.json()['name']['en_GB']
                    
        
#MAIN
vu_af_ids = ['60008734', '60029124', '60117141', '60109852', '60014594']

#set uuids
input_uuids = input('Enter one or more Pure RO UUIDs (comma separated, without spaces) : ')
publ_uuids = input_uuids.split(",")

#df log files
df_log = pd.DataFrame(columns=['date','uuid','get_pure_record','get_openalex_record', 'get_doaj_record', 'get_crossref_record', 'write_keyw', 'write_electr_versions', 'write_publ_status', 'write_contrib_status'])
df_oa_values = pd.DataFrame(columns=['uuid', 'pure_id', 'doi', 'journal_issn', 'pub_yr_first' ,'unl_status_pure', 'openalex_oa_status', 'openalex_doaj_status', 'openalex_license', 'doaj_start', 'doaj_apc', 'doaj_journal', 'unl_status_new', 'oa_colour_new'])
df_crossref = pd.DataFrame(columns=['status-code', 'doi', 'type', 'publisher', 'license-list', 'created_pub_year', 'created_pub_month', 'created_pub_day', 'print_pub_year', 'print_pub_month', 'print_pub_day', 'online_pub_year', 'online_pub_month', 'online_pub_day', 'issued_pub_year', 'issued_pub_month', 'issued_pub_day', 'issue_pub_year', 'issue_pub_month', 'issue_pub_day', 'indexed_year', 'indexed_month', 'indexed_day'])
df_openalex = pd.DataFrame(columns=['openalex.id', 'doi', 'pub_year', 'pub_date', 'pub_month', 'pub_day', 'main_title', 'sub_title', 'oa_status', 'prim_loc_landing', 'prim_loc_pdf', 'prim_loc_is_oa', 'prim_loc_in_doaj', 'prim_loc_license', 'prim_loc_version', 'green_url_landing', 'green_url_license', 'vor_pdf_url', 'vor_pdf_license' ,'pmc_loc_landing', 'pmc_loc_pdf', 'pmc_loc_is_oa', 'pmc_loc_license', 'pmc_loc_version', 'journal', 'issn', 'volume', 'issue', 'first_page', 'last_page'])
df_persons_missing_auid = pd.DataFrame(columns=['publ uuid', 'title', 'sub-title', 'person uuid', 'scopus AU-ID'])
df_scopus_auth_not_in_pure = pd.DataFrame(columns=['au-id', 'au-surnm', 'au-fname', 'af-ids'])
df_intern_person_removed = pd.DataFrame(columns=['publ uuid', 'title', 'sub-title', 'person uuid', 'scopus lname', 'scopus fname', 'scopus AU-ID', 'has VU-affil'])

#create session log directory
file_dir = sys.path[0]
path_session_add = 0
path_session = os.path.join(file_dir, 'log_files', str(datetime.datetime.now().strftime('%Y-%m-%d')))
while os.path.exists(path_session) == True:
    path_session_add += 1
    path_session = f"{os.path.join(file_dir, 'log_files', str(datetime.datetime.now().strftime('%Y-%m-%d')))}_{str(path_session_add)}"
os.makedirs (path_session)
#get internal person records from Pure as df
int_person_df = get_pure_internal_persons()[5]

#loop through uuids
for n, publ_uuid in enumerate(publ_uuids):
    print ('processing ', publ_uuid, n+1, 'of', len(publ_uuids))
    
    #create pub dir
    path_pub = os.path.join(path_session, str(publ_uuid))
    os.makedirs (path_pub)

    #GET DATA FROM VARIOUS SOURCES
    
    #get pure publication record
    pure_record = getPure(publ_uuid)
    print ('get pure record: ', pure_record.status)
    
    #get crossref data
    crossref_record = getCrossref(pure_record.doi)
    df_crossref.loc[len(df_crossref.index)] = [crossref_record.status, pure_record.doi, crossref_record.type, crossref_record.publisher, crossref_record.licenses, crossref_record.created_year, crossref_record.created_month, crossref_record.created_day, crossref_record.print_year, crossref_record.print_month, crossref_record.print_day, crossref_record.online_year, crossref_record.online_month, crossref_record.online_day, crossref_record.issued_year, crossref_record.issued_month, crossref_record.issued_day, crossref_record.issue_year, crossref_record.issue_month, crossref_record.issue_day, crossref_record.indexed_year, crossref_record.indexed_month, crossref_record.indexed_day]
    print ('crossref: ', crossref_record.status)
       
    #get openalex data
    openalex_record = getOpenalex(pure_record.doi)
    df_openalex.loc[len(df_openalex.index)] = [openalex_record.id, openalex_record.doi, openalex_record.pub_year, openalex_record.pub_date, openalex_record.pub_month, openalex_record.pub_day, openalex_record.main_title, openalex_record.sub_title, openalex_record.oa_status, openalex_record.prim_loc_landing, openalex_record.prim_loc_pdf, openalex_record.prim_loc_is_oa, openalex_record.prim_loc_in_doaj, openalex_record.prim_loc_license, openalex_record.prim_loc_version, openalex_record.green_url_landing, openalex_record.green_url_license, openalex_record.vor_pdf_url, openalex_record.vor_pdf_license, openalex_record.pmc_loc_landing, openalex_record.pmc_loc_pdf, openalex_record.pmc_loc_is_oa, openalex_record.pmc_loc_license, openalex_record.pmc_loc_version, openalex_record.journal, openalex_record.issn, openalex_record.volume, openalex_record.issue, openalex_record.first_page, openalex_record.last_page]
    print ('openalex: ', openalex_record.status)
    
    #get doaj data
    doaj_record = getDOAJ(pure_record.journal_issn)
    print ('doaj: ', doaj_record.status)

    #get scopus record
    scopus_record = getScopus(pure_record.scopus_eid)
    print ('scopus: ', scopus_record.status)

    #RUN FUNCTIONS TO CREATE JSON UPDATES FOR PURE
    
    if scopus_record.status == 200:
        #analyze scopus contributor section against dataframe of all internal pure-person records
        scopus_analysis = analyze_scopus_contrib(scopus_record, int_person_df, pure_record)
        scopus_contrib = scopus_analysis[0]
        scopus_ext_org_df = scopus_analysis[1]
        scopus_ext_person_df = scopus_analysis[2]
        df_scopus_auth_not_in_pure = pd.concat([df_scopus_auth_not_in_pure, scopus_analysis[3]])
        df_persons_missing_auid = pd.concat([df_persons_missing_auid, scopus_analysis[4]])
        #create new contributor section based on analyzed scopus record
        contrib_upd = create_scopus_contrib(pure_record, scopus_contrib, scopus_ext_org_df, scopus_ext_person_df)
        contrib_upd_json = contrib_upd[0]
        #add internal person records that were removed from publication record to df log
        df_intern_person_removed = pd.concat([df_intern_person_removed, contrib_upd[1]])

    publ_status_upd = set_publ_status_update (pure_record, crossref_record)
    publ_status_upd_json = publ_status_upd[0]
    publ_status_upd_list = publ_status_upd[1]
    
    keyw_upd = set_keyword_update (pure_record, openalex_record, doaj_record)
    keyw_upd_json = keyw_upd[0]
    keyw_upd_list = keyw_upd[1]
    
    ev_upd = set_ev_update (pure_record, openalex_record)
    ev_upd_json = ev_upd[0]
    ev_upd_list = ev_upd[1]
    
    #log json record before updates
    open(os.path.join(path_pub, f"{publ_uuid}_before.json"), 'w').write(json.dumps(pure_record.json, indent = 4))
        
    #WRITE TO PURE

    #update publication statuses
    if publ_status_upd_list != []:
        #log json
        open(os.path.join(path_pub, f"{publ_uuid}_publ_status_upd.json"), 'w').write(publ_status_upd_json)
        #write
        response_put_publ_status = requests.put(PURE_BASE_URL+'/ws/api/research-outputs/'+publ_uuid, data = publ_status_upd_json, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        if response_put_publ_status.ok:
            put_publ_status_log = publ_status_upd_list
        else:
            put_publ_status_log = response_put_publ_status.status_code
    else:
        put_publ_status_log = 'N/A'
    print ('update publ status: ', put_publ_status_log)
        
    #update keyword section
    if keyw_upd_list != []:
        #log json
        open(os.path.join(path_pub, f"{publ_uuid}_keyw_upd.json"), 'w').write(keyw_upd_json)
        #write
        response_put_keyw = requests.put(PURE_BASE_URL+'/ws/api/research-outputs/'+publ_uuid, data = keyw_upd_json, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        if response_put_keyw.ok:
            put_keyw_log = keyw_upd_list
        else:
            put_keyw_log = response_put_keyw.status_code
    else:
        put_keyw_log = 'N/A'
    print ('update keyw: ', put_keyw_log)

    #update electronic version section
    if ev_upd_list != []:
        #log json
        open(os.path.join(path_pub, f"{publ_uuid}_ev_upd.json"), 'w').write(ev_upd_json)
        #write
        response_put_doi = requests.put(PURE_BASE_URL+'/ws/api/research-outputs/'+publ_uuid, data = ev_upd_json, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        if response_put_doi.ok:
            put_doi_log = ev_upd_list
        else:
            put_doi_log = response_put_doi.status_code
    else:
        put_doi_log = 'N/A'
    print ('update ev-doi: ', put_doi_log)

    #update contribution section
    if scopus_record.status == 200:
        open(os.path.join(path_pub, f"{publ_uuid}_contrib_upd.json"), 'w').write(contrib_upd_json)
        #write
        response_put_contrib = requests.put(PURE_BASE_URL+'/ws/api/research-outputs/'+publ_uuid, data = contrib_upd_json, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
        
        put_contrib_log = response_put_contrib.status_code
        
    else:
        put_contrib_log = 'N/A'
    print ('update contrib section: ', put_contrib_log)
          
    #log json publ after update
    if put_publ_status_log == 'N/A' and put_keyw_log == 'N/A' and put_doi_log == 'N/A':
        pass
    else:
        pure_record = getPure(publ_uuid)
        open(os.path.join(path_pub, f"{publ_uuid}_after.json"), 'w').write(json.dumps(pure_record.json, indent = 4))

    df_log.loc[len(df_log.index)] = [datetime.datetime.now(), publ_uuid,pure_record.status, openalex_record.status, doaj_record.status, crossref_record.status, put_keyw_log, put_doi_log, put_publ_status_log, put_contrib_log]   
    df_oa_values.loc[len(df_oa_values.index)] = [publ_uuid, pure_record.pure_id, pure_record.doi, pure_record.journal_issn, pure_record.pub_yr_first, keyw_upd[2], openalex_record.oa_status, openalex_record.prim_loc_in_doaj, openalex_record.prim_loc_license, doaj_record.doaj_start, doaj_record.has_apc, doaj_record.doaj_journ, keyw_upd[3], '']


enrich_df_removed_persons (df_intern_person_removed, int_person_df)



#write operations log
df_log.to_csv(os.path.join(path_session, "operations_log.csv"), encoding='utf-8', index = False)
df_crossref.to_csv(os.path.join(path_session, "crossref_data.csv"), encoding='utf-8', index = False)
df_openalex.to_csv(os.path.join(path_session, "openalex_data.csv"), encoding='utf-8', index = False)
df_oa_values.to_csv(os.path.join(path_session, "oa_values_log.csv"), encoding='utf-8', index = False)
df_persons_missing_auid.to_csv(os.path.join(path_session, "internal_persons_without_scopus_AU-ID.csv"), encoding='utf-8', index = False)
df_scopus_auth_not_in_pure.to_csv(os.path.join(path_session, "scopus_vu_auid_not_in_pure.csv"), encoding='utf-8', index = False)
df_intern_person_removed.to_csv(os.path.join(path_session, "internal_persons_removed_from_publ.csv"), encoding='utf-8', index = False)

