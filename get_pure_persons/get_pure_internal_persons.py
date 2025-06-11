
def get_pure_internal_persons():

    from config import PURE_BASE_URL, PURE_524_API_KEY
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os, sys
    import requests
    import json
    import csv
    import xlrd
    import math
    from IPython.display import clear_output
    import datetime
    import pandas

    #get person affiliations and IDs from Pure
    
    int_person_list = []
    int_person_dict = {}
    person_scopus_ids = []
    scopus_id2affil = {}
    pure_scopus_ids = []

    #url_person = "https://research.vu.nl/ws/api/524/persons?"
    url_person = PURE_BASE_URL+"/ws/api/524/persons?"
    """
    while True:
        pick = input("get only active staff? yes/no ").lower()
        if pick[0] == 'y':
            print("get active")
            url_person = "https://research.vu.nl/ws/api/524/persons/active?"
            break
        elif pick[0] == 'n':
            print("get all")
            url_person = "https://research.vu.nl/ws/api/524/persons?"
            break
        else:
            print("You have to choose Yes or No")
    """

    def get_response(offset, size):
        try:
            
            response = requests.get(url_person, headers={'Accept': 'application/json'},params={'size': size, 'offset':offset, 'apiKey':PURE_524_API_KEY})
            
            for count,item in enumerate(response.json()['items'][0:]):  
                                      
                    count_scopus = 1
                    count_photo = 0

                    photo_type_ok = "false"
                    youshare_candidate = "false"
                    person_scopus_ids = []
                    person_affil_list = []
                    name_list = []
                    affil_first_dt = datetime.datetime(9999, 12, 31)
                    affil_last_dt = datetime.datetime(1900, 1, 1)
                    fname_knownas = lname_knownas = None
                    
                    if 'externalId' in item:
                        vunetid = item['externalId']
                    else:
                        vunetid = ""
                    
                    #get names
                    fname_def = item['name']['firstName']
                    lname_def = item['name']['lastName']
                    if 'nameVariants' in item:
                        for name_variant in item['nameVariants']:
                            nv_type = name_variant['type']['uri']
                            fn_nv = name_variant['name'].get('firstName')
                            ln_nv = name_variant['name'].get('lastName')
                            name_list.append({'namevar_type': nv_type, 'namevar_fname': fn_nv, 'namevar_lname': ln_nv})
                            if nv_type == '/dk/atira/pure/person/names/knownas':
                                fname_knownas = fn_nv
                                lname_knownas = ln_nv
                            else:
                                continue
                    else:
                        continue
                    
                    #get affiliations
                    for affil in item['staffOrganisationAssociations']:
                            affil_start_dt = datetime.datetime.strptime(affil['period']['startDate'][:10], '%Y-%m-%d')
                            if 'endDate' in affil['period']:
                                affil_end_dt = datetime.datetime.strptime(affil['period']['endDate'][:10], '%Y-%m-%d')
                            else: affil_end_dt = datetime.datetime(9999, 12, 31)
                            if 'jobTitle' in affil:
                                job_title = affil['jobTitle']['uri'][affil['jobTitle']['uri'].rfind("/")+1:]
                            else: job_title = ''
                            if 'emails' in affil:
                                email = affil['emails'][0]['value']['value']
                            else: email = ''
                            person_affil_list.append({'af_id':affil['pureId'],'af_org_id':affil['organisationalUnit']['uuid'], 'af_org_name':affil['organisationalUnit']['name']['text'], 'af_source_id':affil['organisationalUnit']['externalId'], 'af_start':affil_start_dt,'af_end':affil_end_dt, 'job_title':job_title,'e_mail':email})
                            if affil_start_dt < affil_first_dt:
                                affil_first_dt = affil_start_dt
                            if affil_end_dt > affil_last_dt:
                                affil_last_dt = affil_end_dt

                    #get scopus-IDs
                    if 'ids' in item:
                        for ct, extid in enumerate (item['ids']):
                            if item['ids'][ct]['type']['term']['text'][0]['value'] == 'Scopus Author ID':
                                person_scopus_ids.append(item['ids'][ct]['value']['value'])
                                pure_scopus_ids.append(item['ids'][ct]['value']['value'])
                                #create index scopus-ID + affiliation_list
                                scopus_id2affil[item['ids'][ct]['value']['value']] = person_affil_list
                                count_scopus += 1    

                    #determine YouShare-status
                    if 'keywordGroups' in item:
                        for keyword_group in item['keywordGroups']:
                            if keyword_group['logicalName'] =="/dk/atira/pure/keywords/You_Share_Participant":
                                youshare_candidate = "true"
                            else:
                                youshare_candidate = "false"

                    #determine profile photo status
                    if 'profilePhotos' in item:
                        
                        for photo in item['profilePhotos']:
                            count_photo += 1
                            if 'type' in photo:
                                if photo['type']['uri'] == '/dk/atira/pure/person/personfiles/portrait':
                                    photo_type_ok = 'true'               
                                else:
                                    pass
                            else:
                                pass
                    else:
                        photo_type_ok = 'NA'

                    
                    int_person_list.append({'person_uuid':item['uuid'], 'person_pure_id': item['pureId'], 'vunetid':vunetid, 'youshare':youshare_candidate,'scopus_ids':person_scopus_ids,'personaffiliations':person_affil_list, 'affil_first_dt': affil_first_dt, 'affil_last_dt': affil_last_dt,'default_fname': fname_def, 'default_lname': lname_def, 'knownas_fname': fname_knownas, 'knownas_lname': lname_knownas, 'name_list': name_list, 'photo_ok': photo_type_ok, 'photo_count': count_photo, 'visibility': item['visibility']['key']})                         
                    int_person_dict[item['uuid']] = {'person_uuid':item['uuid'], 'person_pure_id': item['pureId'], 'youshare':youshare_candidate,'scopus_ids':person_scopus_ids,'personaffiliations':person_affil_list, 'affil_first_dt': affil_first_dt, 'affil_last_dt': affil_last_dt,'default_fname': fname_def, 'default_lname': lname_def, 'knownas_fname': fname_knownas, 'knownas_lname': lname_knownas, 'name_list': name_list, 'photo_ok': photo_type_ok, 'photo_count': count_photo, 'visibility': item['visibility']['key']}
            
            return int_person_list, int_person_dict, person_scopus_ids, scopus_id2affil, pure_scopus_ids
        except requests.exceptions.RequestException as e:
            print (e)
            return e
     
    def runner():
        size = 1000
        offset = 0
        response = requests.get(url_person, headers={'Accept': 'application/json'},params={ 'apiKey':PURE_524_API_KEY})
        
        no_records = (response.json()['count'])
        cycles = (math.ceil(no_records/size))
        print (f"getting {no_records} person records from Pure in {cycles} cycles")
        
        threads= []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for request in range (cycles)[0:]:
                threads.append(executor.submit(get_response, offset, size))
                offset += size
                
            for task in as_completed(threads):
                print (f"got {len(int_person_list)} of {no_records} records")
                #clear_output('wait') 
          
    runner()

    person_df_1 = pandas.DataFrame.from_dict(int_person_list).explode('scopus_ids')
    #person_df_1.to_excel('uuid_list.xls', index=False)
    #person_df_2 = pandas.DataFrame.from_dict(scopus_id2affil, orient = 'index')
    #person_df_3 = pandas.DataFrame.from_dict(int_person_dict, orient = 'index')
    #person_df_2.to_excel('scopus_dict.xls', index=True)
    #person_df_3.to_excel('uuid_dict.xls', index=True)
    
        
    return int_person_list, int_person_dict, person_scopus_ids, scopus_id2affil, pure_scopus_ids, person_df_1

#get_pure_internal_persons()

