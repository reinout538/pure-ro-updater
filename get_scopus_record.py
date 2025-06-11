import requests
import json
import pandas as pd
import os, sys
import csv

from config import*

def get_scopus(EID):
    
    url_scopus = ("https://api.elsevier.com/content/abstract/eid/2-s2.0-" + EID + "?")
    
    response_scopus = requests.get(url_scopus, headers={'Accept': 'application/json'},params={'apiKey':SCOPUS_API_KEY})
    if response_scopus.status_code == 200:  
        json_scopus = response_scopus.json()['abstracts-retrieval-response']
    else:
        json_scopus = None
    
    return json_scopus, response_scopus.status_code

class getScopus():
    
    def __init__(self, EID):

        if EID is None:
            self.status = "no eid"
            self.set_all_none()
            return

        json_scopus = get_scopus(EID)[0]
        self.status = get_scopus(EID)[1]

        if json_scopus != None:
            self.type = self.get_type(json_scopus)
            self.sub_type = self.get_subtype(json_scopus)
            self.pub_year = self.get_pub_date(json_scopus)[0]
            self.pub_month = self.get_pub_date(json_scopus)[1]
            self.pub_day = self.get_pub_date(json_scopus)[2]
            self.doi = self.get_doi(json_scopus)
            self.oa_flag = self.get_oa_flag(json_scopus)
            self.main_title = self.get_title(json_scopus)[0]
            self.sub_title = self.get_title(json_scopus)[1]
            self.abstract = self.get_abstract(json_scopus)
            self.affil_org = self.get_affil_org(json_scopus)
            self.contrib = self.get_persons(json_scopus)[0]
            self.mixed_affil = self.get_persons(json_scopus)[1]
            self.collab = self.get_collab(json_scopus)
            self.pages = self.get_pages(json_scopus)
            self.no_pages = self.get_no_pages(json_scopus)
            self.issue = self.get_issue(json_scopus)
            self.volume = self.get_volume(json_scopus)
            self.art_no = self.get_art_no(json_scopus)
            self.journal = self.get_journal(json_scopus)
            self.isbn = self.get_isbn(json_scopus)
            self.publisher = self.get_publisher(json_scopus)
            self.proc_title = self.get_proc_title(json_scopus)
            self.host_title = self.get_host_title(json_scopus)
            self.editors = self.get_editors(json_scopus)
            self.series_issns = self.get_series_issns(json_scopus)
            self.event_name = self.get_event_name(json_scopus)
            self.event_start_date = self.get_event_date(json_scopus)[0]
            self.event_end_date = self.get_event_date(json_scopus)[1]
            self.event_country = self.get_event_location(json_scopus)[0]
            self.event_city = self.get_event_location(json_scopus)[1]
            self.extorg_country = self.get_extorg_country(json_scopus)
            self.corresp_author = self.get_correspondence(json_scopus)
        else:
            self.set_all_none()

    def set_all_none(self):
        # Helper function to initialize all attributes to None
        self.type = self.sub_type = self.pub_year = self.pub_month = self.pub_day = self.doi = self.oa_flag = self.main_title = self.sub_title = self.abstract = self.affil_org = self.contrib = self.mixed_affil = self.collab = self.pages = self.no_pages = self.issue = self.volume = self.art_no = self.journal = self.isbn = self.publisher = self.proc_title = self.host_title = self.editors = self.series_issns = self.event_name = self.event_start_date = self.event_end_date = self.event_country = self.event_city = self.extorg_country = self.corresp_author = None
            
    def get_type(self, json_scopus):
        return json_scopus['coredata']['srctype']
        
    def get_subtype(self, json_scopus): 
        return json_scopus['coredata']['subtype']
        
    def get_pub_date(self, json_scopus):
        pub_date = json_scopus['item']['bibrecord']['head']['source']['publicationdate']
        pub_dt_yr = pub_date['year']
        if 'month' in pub_date:
            pub_dt_mo = pub_date['month']
        else: pub_dt_mo = None
        if 'day' in pub_date:
            pub_dt_day = pub_date['day']
        else: pub_dt_day = None
        
        return pub_dt_yr, pub_dt_mo, pub_dt_day 
    
    def get_title(self, json_scopus):
        if 'dc:title' in json_scopus['coredata']:
            full_title = json_scopus['coredata']['dc:title']   
            if ":" in full_title: 
                main_title = full_title.split(":",1)[0]
                sub_title = full_title.split(":",1)[1].lstrip()
            else: 
                main_title = full_title
                sub_title = None
        else:
            main_title = ""
            sub_title = None
            
        return main_title, sub_title
    
    def get_abstract(self, json_scopus):
        if 'dc:description' in json_scopus['coredata']:
            abstract = json_scopus['coredata']['dc:description']
        else: abstract = None
        
        return abstract

    def get_doi(self, json_scopus):
        doi = json_scopus['coredata'].get('prism:doi')
        return doi
    
    def get_oa_flag(self, json_scopus):
        oa_flag = json_scopus['coredata'].get('openaccessFlag')
        return oa_flag

    def get_affil_org(self, json_scopus):

        #affilatiegegevens ophalen indien aanwezig

        affil_dict = {}        
        if 'affiliation' in json_scopus:
        
            affil_data = json_scopus['affiliation']

            #affilData kan list ofwel dict zijn (indien er maar 1 is)
            if isinstance(affil_data,list):
                for affiliation in affil_data:
                    aff_id = affiliation['@id']
                    affil_dict[aff_id] = {'affil_name':affiliation['affilname'],'affil_country':affiliation['affiliation-country']}

            if isinstance(affil_data,dict):
                aff_id = affil_data['@id']
                affil_dict[aff_id] = {'affil_name':affil_data['affilname'],'affil_country':affil_data['affiliation-country']}
        print (affil_dict)
        return affil_dict
        
    def get_persons(self, json_scopus):
        
        author_list = []
        authors_json = json_scopus['authors']['author']
        
        affil_dict = self.get_affil_org(json_scopus)
        #author_dict[au_id] = {'au-id':au_id,'au-seq':au_seq, 'au-surnm':au_surnm, 'au-init':au_init, 'au-index-nm':au_index_nm, 'au-orcid':au_orcid, 'au-affils':[], 'pure-uuid': None}
        corresp_author_list = self.get_correspondence(json_scopus)
              
        for i, auth in enumerate(authors_json):
            auth_id=auth['@auid']
            if 'ce:given-name' in auth:
                auth_firstname = auth.get('ce:given-name')
            else:
                auth_firstname = auth.get('ce:initials')
            auth_lastname = auth['ce:surname']
            if 'ce:indexed-name' in auth:
                auth_indexed_name = auth['ce:indexed-name']
                if auth_indexed_name in corresp_author_list:
                    corr_author = True
                else:
                    corr_author = False
            else:
                auth_indexed_name = None
                corr_author = False
                
            person_affil = []
             
            #
            if auth.get('affiliation') != None:
                if isinstance(auth['affiliation'], list):
                    org_list = []
                    for affil in auth['affiliation']:                
                        affil_id = affil['@id']
                        affil_name = affil_dict[affil_id]['affil_name']
                        affil_country = affil_dict[affil_id]['affil_country']
                        if affil_id not in org_list:
                            org_list.append(affil_id)
                            person_affil.append({'affil_id':affil_id, 'org_name':affil_name, 'org_country':affil_country})
                                                                        
                if isinstance(auth['affiliation'], dict):        
                    affil_id = auth['affiliation']['@id']
                    affil_name = affil_dict[affil_id]['affil_name']
                    affil_country = affil_dict[affil_id]['affil_country']
                    person_affil.append({'affil_id':affil_id, 'org_name':affil_name, 'org_country':affil_country})
                                  
                    
            else:
                pass                              
            author_list.append({'auth_id':auth_id, 'auth_first_name':auth_firstname, 'auth_last_name':auth_lastname, 'auth_is_corresp': corr_author, 'auth_affil':person_affil})

            #determine mixed affil situation: some authors DO have affiliation and others DON'T (typical when author collaboration is present)
            all_auth_have_affil = True
            no_auth_has_affil = True
            for author in author_list:
                if author['auth_affil'] == []:
                    all_auth_have_affil = False
                else:
                    no_auth_has_affil = False
            if all_auth_have_affil == False and no_auth_has_affil == False:
                mixed_affil_situation = True
            else:
                mixed_affil_situation = False

        return author_list, mixed_affil_situation
        
                
    def get_collab(self, json_scopus):
        
        collab_list = []
        author_groups = json_scopus['item']['bibrecord']['head']['author-group']
        
        #get author collaboration if present (assuming this is always a list not a dict)
        if isinstance(author_groups,list):
                        
            for g, group in enumerate((author_groups)):
                
                if 'collaboration' in author_groups[g]:
                    if isinstance(author_groups[g]['collaboration'],list):
                        for collab in author_groups[g]['collaboration']:
                            collab_list.append(collab['ce:indexed-name'])
                    if isinstance(author_groups[g]['collaboration'],dict):
                        collab_list.append(author_groups[g]['collaboration']['ce:indexed-name'])

        return collab_list
    
    def get_pages(self, json_scopus):
        pages = json_scopus['coredata'].get('prism:pageRange')
        return pages
    
    def get_no_pages(self, json_scopus):
        try:
            no_pages = json_scopus['coredata']['prism:endingPage'] - json_scopus['coredata']['prism:startingPage']
        except: no_pages = None
        return no_pages
    
    def get_issue(self, json_scopus):
        issue = json_scopus['coredata'].get('prism:issueIdentifier')
        return issue
    
    def get_volume(self, json_scopus):
        volume = json_scopus['coredata'].get('prism:volume')
        return volume
    
    def get_art_no(self, json_scopus):
        art_no = json_scopus['coredata'].get('article-number')
        return art_no
    
    def get_journal(self, json_scopus):

        subtypes_journ = {"ar", "dp","no", "ed", "er", "le", "sh", "re"}
        if json_scopus['coredata']['subtype'] in subtypes_journ and json_scopus['coredata']['srctype'] != 'b':
        
            journal_dict = {}

            journal_name = json_scopus['item']['bibrecord']['head']['source']['sourcetitle']
            journal_dict['journal_name'] = journal_name

            issns = json_scopus['item']['bibrecord']['head']['source'].get('issn')

            if isinstance(issns, list):

                for issn in issns:

                    if issn.get('@type') == 'print':
                        print_issn = issn.get('$')[:4]+'-'+issn.get('$')[-4:]
                        journal_dict['print_issn'] = print_issn

                    if issn.get('@type') == 'electronic':
                        electronic_issn = issn.get('$')[:4]+'-'+issn.get('$')[-4:]
                        journal_dict['electronic_issn'] = electronic_issn

            if isinstance(issns, dict):

                if issns.get('@type') == 'print':
                    print_issn = issns.get('$')[:4]+'-'+issns.get('$')[-4:]
                    journal_dict['print_issn'] = print_issn

                if issns.get('@type') == 'electronic':
                    electronic_issn = issns.get('$')[:4]+'-'+issns.get('$')[-4:] 
                    journal_dict['electronic_issn'] = electronic_issn

            return journal_dict
        
    def get_isbn(self, json_scopus):
        isbn = json_scopus['coredata'].get('prism:isbn')
        
        if 'isbn' in json_scopus['item']['bibrecord']['head']['source']:
            isbns = json_scopus['item']['bibrecord']['head']['source']['isbn']
            isbn_list = []
            if isinstance(isbns, list):

                for isbn in isbns:

                    if isbn.get('@type') == 'print':
                        isbn_list.append({'type':'print', 'value':isbn['$']}) 
                    if isbn.get('@type') == 'electronic':
                        isbn_list.append({'type':'electronic', 'value':isbn['$']}) 

            if isinstance(isbns, dict):

                if isbns.get('@type') == 'print':
                        isbn_list.append({'type':'print', 'value':isbns['$']}) 
                if isbns.get('@type') == 'electronic':
                        isbn_list.append({'type':'electronic', 'value':isbns['$']}) 

            return isbn_list

        return isbn
    
    def get_publisher(self, json_scopus):
        if 'publisher' in json_scopus['item']['bibrecord']['head']['source']:
            publisher = json_scopus['item']['bibrecord']['head']['source']['publisher']['publishername']
            return publisher
    
    def get_proc_title(self, json_scopus):
        proc_title = json_scopus['item']['bibrecord']['head']['source'].get('issuetitle')
        if proc_title == None:
            proc_title = json_scopus['item']['bibrecord']['head']['source'].get('volumetitle')
        if proc_title == None:
            proc_title = json_scopus['item']['bibrecord']['head']['source'].get('sourcetitle')
        
        return proc_title
    
    def get_host_title(self, json_scopus):
        host_title = json_scopus['item']['bibrecord']['head']['source'].get('sourcetitle')
        
        #exception found in 2-s2.0-85092197299: sourcetitle = dict instead of string
        if isinstance(host_title,dict):
            host_title = host_title['$']
        return host_title
        
    
    def get_editors(self, json_scopus):
        if 'contributor-group' in json_scopus['item']['bibrecord']['head']['source']:
            editor_list = []
            editors = json_scopus['item']['bibrecord']['head']['source']['contributor-group']
            if isinstance(editors, list):
            
                for editor in editors:
                    try:
                        ed_first_name = editor['contributor'].get('ce:initials')
                        ed_last_name = editor['contributor'].get('ce:surname')
                        editor_list.append({'ed_first_name':ed_first_name, 'ed_last_name':ed_last_name})
                    except:
                        continue
                        
            if isinstance(editors, dict):
                try:
                    ed_first_name = editors['contributor'].get('ce:initials')
                    ed_last_name = editors['contributor'].get('ce:surname')
                    editor_list.append({'ed_first_name':ed_first_name, 'ed_last_name':ed_last_name})
                except:
                    #may also be a list inside contributor
                    try:
                        for editor in editors['contributor']:
                            try:
                                ed_first_name = editor.get('ce:initials')
                                ed_last_name = editor.get('ce:surname')
                                editor_list.append({'ed_first_name':ed_first_name, 'ed_last_name':ed_last_name})
                            except:
                                continue
                    except:
                        pass
                        
            return editor_list
    
        
    def get_series_issns(self, json_scopus):
        if 'issn' in json_scopus['item']['bibrecord']['head']['source']:
            series_issns = json_scopus['item']['bibrecord']['head']['source']['issn']
            series_issn_list = []
            if isinstance(series_issns, list):

                for issn in series_issns:

                    if issn.get('@type') == 'print':
                        series_issn_list.append({'type':'print', 'value':f"{issn['$'][:4]}-{issn['$'][-4:]}"}) 

                    if issn.get('@type') == 'electronic':
                        series_issn_list.append({'type':'electronic', 'value':f"{issn['$'][:4]}-{issn['$'][-4:]}"}) 

            if isinstance(series_issns, dict):

                if series_issns.get('@type') == 'print':
                        series_issn_list.append({'type':'print', 'value':f"{series_issns['$'][:4]}-{series_issns['$'][-4:]}"}) 

                if series_issns.get('@type') == 'electronic':
                        series_issn_list.append({'type':'electronic', 'value':f"{series_issns['$'][:4]}-{series_issns['$'][-4:]}"}) 

            return series_issn_list

    def get_event_name(self, json_scopus):
        try:
            event_name = json_scopus['item']['bibrecord']['head']['source']['additional-srcinfo']['conferenceinfo']['confevent']['confname']
        except:
            event_name = None
        
        return event_name
    
    def get_event_date(self, json_scopus):
        try:
            event_start_dt = json_scopus['item']['bibrecord']['head']['source']['additional-srcinfo']['conferenceinfo']['confevent']['confdate']['startdate']
            event_start = f"{event_start_dt['@day']}-{event_start_dt['@month']}-{event_start_dt['@year']}"
        except:
            event_start = None
        try:
            event_end_dt = json_scopus['item']['bibrecord']['head']['source']['additional-srcinfo']['conferenceinfo']['confevent']['confdate']['enddate']
            event_end = f"{event_end_dt['@day']}-{event_end_dt['@month']}-{event_end_dt['@year']}"
        except: event_end = None
            
        return event_start,event_end
    
    def get_event_location(self, json_scopus):
        try:
            event_country_scopus = json_scopus['item']['bibrecord']['head']['source']['additional-srcinfo']['conferenceinfo']['confevent']['conflocation']['@country']
            event_country = pycountry_convert.country_alpha3_to_country_alpha2(event_country_scopus.upper()).lower()
        except: 
            event_country = None
        try:
            event_city = json_scopus['item']['bibrecord']['head']['source']['additional-srcinfo']['conferenceinfo']['confevent']['conflocation']['city']
        except: event_city = None
            
        return event_country, event_city
    
    def get_extorg_country(self, json_scopus):
        
        author_group = json_scopus['item']['bibrecord']['head']['author-group']
                
        for group in author_group:
            if 'affiliation' in group:
                try:
                    ext_org_country = pycountry_convert.country_alpha3_to_country_alpha2(group['affiliation']['@country'].upper()).lower()
                    ext_org_dict[group['affiliation']['@afid']] = ext_org_country
                                
                except: pass
    
    def get_correspondence(self, json_scopus):

        corresp_auth = []
        if 'correspondence' in json_scopus['item']['bibrecord']['head']:
            if isinstance(json_scopus['item']['bibrecord']['head']['correspondence'], list):
                for corresp in json_scopus['item']['bibrecord']['head']['correspondence']:
                    if 'person' in json_scopus['item']['bibrecord']['head']['correspondence']:
                        corresp_auth.append(corresp['person']['ce:indexed-name'])
            if isinstance(json_scopus['item']['bibrecord']['head']['correspondence'], dict):
                if 'person' in json_scopus['item']['bibrecord']['head']['correspondence']:
                    corresp_auth.append(json_scopus['item']['bibrecord']['head']['correspondence']['person']['ce:indexed-name'])
        else:
            pass

        return corresp_auth

"""
#try it out

file_dir = sys.path[0]

EID_list = ['84907821888']

df_scopus = pd.DataFrame(columns=['eid', 'status', 'contrib'])

for n, EID in enumerate(EID_list):

    print (n, EID)
    
    scopus = getScopus(EID)
    print (scopus.mixed_affil)
    
    df_scopus.loc[len(df_scopus.index)] = [EID, scopus.status, scopus.contrib]
    df_scopus.to_csv(os.path.join(file_dir, "scopus_data.csv"), encoding='utf-8', index = False)
"""

