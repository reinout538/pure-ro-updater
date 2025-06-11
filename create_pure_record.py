import os, sys
import csv
import math
import pandas as pd
import requests
import json

from config import PURE_BASE_URL, PURE_CRUD_API_KEY

file_dir = sys.path[0]

def get_uri_country(org_country):

    country_uri = None
    response_allowed_countries = requests.get(PURE_BASE_URL+'/ws/api/external-organizations/allowed-address-countries', headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key': PURE_CRUD_API_KEY})
    
    for country in response_allowed_countries.json()["classifications"]:
        if country["term"]["en_GB"] == org_country:
            country_uri = country["uri"]
        else:
            continue

    return country_uri

def create_ext_org(org_id, org_name, org_country):
  
    country_uri = get_uri_country(org_country)
    
    json_extorg = json.dumps(
            {
            "name": {"en_GB": org_name},
            "type": {"uri": "/dk/atira/pure/ueoexternalorganisation/ueoexternalorganisationtypes/ueoexternalorganisation/unknown",
                    "term": {"en_GB": "Unknown"}},
            "identifiers": [
                {"typeDiscriminator": "ClassifiedId",
                "id": org_id,
                "type": {"uri": "/dk/atira/pure/ueoexternalorganisation/ueoexternalorganisationsources/scopus_affiliation_id",
                        "term": {"en_GB": "Scopus affiliation ID"}
                        }
                }
              ],
            "address": {
                "country": {
                    "uri": country_uri,
                    "term": {"en_GB": org_country}
                            }
                        },
            "visibility": {
                "key": "FREE",
                "description": {"en_GB": "Public - No restriction"}
                          },
            "workflow": {"step": "approved",
                        "description": {"en_GB": "Approved"}
                        },
            "systemName": "ExternalOrganization"
            }
            )

    create_extorg = requests.put(PURE_BASE_URL+'/ws/api/external-organizations/', data = json_extorg, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key':PURE_CRUD_API_KEY})
    return (create_extorg.json()['uuid'])

def create_ext_person(au_id, au_surn, au_fname):
    
    json_extpers = json.dumps({
      "identifiers": [
        {
          "typeDiscriminator": "ClassifiedId",
          "id": au_id,
          "type": {
            "uri": "/dk/atira/pure/externalperson/externalpersonsources/scopusauthor",
            "term": {
              "en_GB": "Scopus Author ID"
            }
          }
        }
      ],
      "name": {
        "firstName": au_fname,
        "lastName": au_surn
      },
      "type": {
        "uri": "/dk/atira/pure/externalperson/externalpersontypes/externalperson/externalperson",
        "term": {
          "en_GB": "External person"
        }
      },
      "workflow": {
        "step": "forApproval",
        "description": {
          "en_GB": "For approval"
        }
      },
      "systemName": "ExternalPerson"
    }
           
            )

    create_extpers = requests.put(PURE_BASE_URL+'/ws/api/external-persons/', data = json_extpers, headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'api-key':PURE_CRUD_API_KEY})
    return (create_extpers.json()['uuid'])

#main

#create_ext_person("123456789", "Dam", "Reinout")


"""

df_external_persons = pd.DataFrame(columns=['au-id', 'au-surnm','au-fname', 'af-ids'])

"""
