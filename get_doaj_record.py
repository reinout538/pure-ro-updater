import requests
import json



def get_doaj_status(issn):

    doaj_api = 'https://doaj.org/api/search/journals/'

    query = f'issn:{issn}'

    try:
        response_doaj = requests.get(doaj_api+query, headers={'Accept': 'application/json'})

    except requests.exceptions.RequestException as e:
        json_doaj = None
        print (e)
        return e
    
    if response_doaj.status_code == 200:
        doaj_record = response_doaj.json()
    else:
        doaj_record = None

    return (doaj_record, response_doaj.status_code)

class getDOAJ():

    def __init__(self, ISSN):

        if ISSN is None:
            self.status = "no issn"
            self.record_count = self.doaj_journ = self.has_apc = self.doaj_start = None
            return

        doaj_record = get_doaj_status(ISSN)[0]
        self.status = get_doaj_status(ISSN)[1]

        if doaj_record != None and doaj_record['total'] == 1:
            
            self.doaj_journ = True
            self.has_apc = doaj_record['results'][0]['bibjson']['apc']['has_apc']
            self.doaj_start = self.get_doaj_start(doaj_record)
            self.record_count = doaj_record['total']

        else:
            if doaj_record != None:
                self.record_count = doaj_record['total']
                self.doaj_journ = self.has_apc = self.doaj_start = None
            else:
                self.record_count = self.doaj_journ = self.has_apc = self.doaj_start = None

    def get_doaj_start (self, doaj_record):
        
        if 'oa_start' in doaj_record['results'][0]['bibjson']:
            doaj_start = doaj_record['results'][0]['bibjson']['oa_start']
        else: 
            doaj_start = int(doaj_record['results'][0]['created_date'][:4])
                
        return (doaj_start)

"""
doaj = getDOAJ(None)

print (doaj.status, doaj.doaj_journ, doaj.has_apc, doaj.doaj_start, doaj.record_count)
"""
