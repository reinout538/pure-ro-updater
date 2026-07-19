import requests
import json
import pandas as pd
import os, sys
import csv
import time
import pycountry_convert

#from config import*

def get_scopus_person(AUID, scopus_api_key):
    
    url_scopus = ("https://api.elsevier.com/content/search/author?query=AU-ID(" + AUID + ")")
    
    response_scopus = requests.get(url_scopus, headers={'Accept': 'application/json'},params={'apiKey':scopus_api_key})
    if response_scopus.status_code == 200:  
        check = response_scopus.json()['search-results']['opensearch:totalResults']
    else:
        check = None
    
    return check, response_scopus.status_code


def get_scopus(EID, scopus_api_key):
    
    url_scopus = ("https://api.elsevier.com/content/abstract/eid/2-s2.0-" + EID + "?")
    
    response_scopus = requests.get(url_scopus, headers={'Accept': 'application/json'},params={'apiKey':scopus_api_key})
    if response_scopus.status_code == 200:  
        json_scopus = response_scopus.json()['abstracts-retrieval-response']
    else:
        json_scopus = None
    
    return json_scopus, response_scopus.status_code

class getScopus():
    
    def __init__(self, EID, scopus_api_key):

        if EID is None:
            self.status = "no eid"
            self.set_all_none()
            return

        json_scopus = get_scopus(EID, scopus_api_key)[0]
        self.status = get_scopus(EID, scopus_api_key)[1]

        if json_scopus is not None and all(key in json_scopus for key in ['item', 'authors', 'coredata', 'affiliation']):
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
            self.status = 'no (complete) record'

    def set_all_none(self):
        # Helper function to initialize all attributes to None
        self.type = self.sub_type = self.pub_year = self.pub_month = self.pub_day = self.doi = self.oa_flag = self.main_title = self.sub_title = self.abstract = self.affil_org = self.contrib = self.mixed_affil = self.collab = self.pages = self.no_pages = self.issue = self.volume = self.art_no = self.journal = self.isbn = self.publisher = self.proc_title = self.host_title = self.editors = self.series_issns = self.event_name = self.event_start_date = self.event_end_date = self.event_country = self.event_city = self.extorg_country = self.corresp_author = None
            
    def get_type(self, json_scopus):
        return json_scopus['coredata'].get('srctype')
        
    def get_subtype(self, json_scopus): 
        return json_scopus['coredata'].get('subtype')
        
    def get_pub_date(self, json_scopus):
        pub_date = (json_scopus['item']
                .get('bibrecord', {})
                .get('head', {})
                .get('source', {})
                .get('publicationdate', {}))
        return pub_date.get('year'), pub_date.get('month'), pub_date.get('day')
    
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
        
        return affil_dict
        
    def get_persons(self, json_scopus):
        
        author_list = []
        authors_json = (json_scopus.get('authors') or {}).get('author')
        if authors_json is None:
            mixed_affil_situation = False
            return author_list, mixed_affil_situation
        
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
        author_groups = json_scopus['item']['bibrecord']['head'].get('author-group')
        
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
            publisher = json_scopus['item']['bibrecord']['head']['source']['publisher'].get('publishername')
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

        ext_org_dict = {}
        author_group = json_scopus['item']['bibrecord']['head'].get('author-group')
        if author_group is None:
            return ext_org_dict
        for group in author_group:
            if 'affiliation' in group:
                try:
                    ext_org_country = pycountry_convert.country_alpha3_to_country_alpha2(group['affiliation']['@country'].upper()).lower()
                    ext_org_dict[group['affiliation']['@afid']] = ext_org_country            
                except: pass

        return ext_org_dict
    
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

EID_list = ['105019728985']

df_scopus = pd.DataFrame(columns=['eid', 'status', 'contrib'])

for n, EID in enumerate(EID_list):

    print (n, EID)
    
    scopus = getScopus(EID, 'a0ff7557d0c58ceb89469ab5291bfc4d')
    print (scopus.collab)
    
    df_scopus.loc[len(df_scopus.index)] = [EID, scopus.status, scopus.contrib]
    df_scopus.to_csv(os.path.join(file_dir, "scopus_data.csv"), encoding='utf-8', index = False)

"""

"""
#try it out
#check if scopus authorID is ok
file_dir = sys.path[0]

#AUID_list = ['55210910400', '57201417566', '8203159700', '23469675300', '35517636600', '55368665400', '6603061239', '57189215838', '55495155800', '7201501143', '6701314974', '7202894744', '35201811400', '56232982900', '11939766800', '57195454789', '7006730867', '55850555800', '57188750289', '7006508852', '56613487700', '36996904700', '6507841115', '6603269520', '22940424300', '55106078200', '6505746359', '56482336100', '57194911499', '57200234038', '8935838200', '56464821900', '55243559600', '57191910422', '57096102400', '56037244700', '23469229300', '7004336753', '25227769600', '7102575587', '7102271437', '50561829200', '24480411800', '57194119399', '57197303530', '55398074300', '36631516500', '8913692200', '6603405989', '7801353451', '56666989500', '35113027400', '54792915600', '56010018200', '57193953297', '7003615371', '8371581300', '6602415545', '7405294861', '36975080500', '57197033626', '6603486773', '57199344188', '32868230900', '24726075400', '7005291762', '15925485700', '36501829200', '6507947915', '6603519384', '57195054557', '54683925400', '55196716900', '16178312500', '7004058826', '55119858000', '55913584900', '6701441029', '6701395425', '50361165300', '23096910700', '56461828100', '15125280200', '7004999647', '26640450300', '57190716403', '56233863200', '36348293900', '57198435781', '7005429858', '7003731759', '57198779160', '45161652600', '6507007157', '22836783600', '6508288286', '7005776702', '12243322200', '35093805100', '6506487210', '35179901300', '57199599606', '22949992000', '6602244660', '35111223900', '55180112800', '6507211855', '6701391083', '12244407800', '6701746401', '7003841066', '23485325000', '57188854636', '55353312800', '16744708600', '8046135100', '7005379471', '57200304389', '56893760100', '47561882000', '7003737362', '26036677700', '36237943200', '55782590400', '24537235900', '6602390402', '6603022519', '8317813000', '56506649400', '55001808100', '55682540300', '56180773600', '7004547629', '7004024063', '6603274461', '55944549200', '35185666600', '6701866406', '57190073774', '8590481900', '56426886800', '56120665200', '6504287998', '57103504800', '24390847200', '12779455200', '57190423969', '25930547300', '55315277500', '43861209200', '57200605007', '7003271016', '55630258700', '55417257000', '36570750000', '35765922100', '7201964130', '15744815200', '6602616341', '7201351714', '57191915512', '6701657735', '6507412758', '36537108700', '35186718800', '6506344788', '6506376604', '56251395300', '7003389642', '22938985300', '37460951300', '57189418600', '41861262600', '53979418400', '6602340980', '6602174241', '37053671300', '55603536700', '57131561000', '57191041133', '16167267800', '6508204784', '56529757000', '6602198325', '37111397300', '7403350771', '41961884000', '6602305955', '24074111100', '54785436900', '7006275025', '7005048329', '40162564600', '37085065500', '7801684802', '36780553300', '6701354109', '56644349100', '26030730000', '25655519000', '55930345600', '7006709352', '39061001400', '35226932700', '6507847032', '36185629200', '15766700900', '57197699477', '15044584900', '24334303200', '6504719437', '56875220400', '9842465700', '56089229300', '57199354845', '16174482300', '6602610855', '35075917900', '54397392400', '57192192599', '6602003141', '6507637656', '25930439500', '23005823700', '6701828573', '36741527500', '56618374000', '14121023500', '6604056271', '55481257800', '56178053500', '6506534030', '36642936000', '27667452100', '37053328200', '25646146900', '56631681000', '22950897900', '55832174700', '22937447200', '6507407842', '55855362200', '6603436987', '54390369100', '35478030800', '36995822400', '55391121700', '6603498837', '57016368800', '57191474838', '37061961500', '6701521666', '55260191500', '55764338500', '6603486657', '7003959718', '35182686400', '10540613400', '55889587300', '15850561500', '56411832300', '55835103400', '57196758051', '55949222600', '22951320200', '57193737577', '11739955900', '56336449500', '6507305656', '57188697907', '13612668100', '16165033000', '7201536652', '36494118100', '6603003407', '57173995000', '35375512000', '8759615400', '6701473455', '23487789100', '55561647900', '55776780000', '57198001909', '35487580200', '54788563600', '35621812200', '6507847776', '57198006416', '8918173600', '7006483726', '35338674100', '15057250500', '6507310838', '6506060597', '41560979900', '33667914200', '7004009631', '24553870900', '24823671400', '6507100137', '57194658228', '24469209400', '7006756560', '55301455900', '57004703500', '7801602933', '56736496700', '57198303280', '36098142800', '16159202600', '24174764500', '6604015060', '16242738900', '14041249700', '56281253300', '15137664800', '55202531000', '7202330527', '6602970103', '6602572649', '54079713100', '50362072900', '35203474900', '57200309747', '56953743600', '37053766300', '35238214700', '55200333100', '8525198400', '6504362827', '56245117300', '8659092900', '54921958200', '36936575300', '36492024900', '7404438219', '6602206093', '6603919424', '21743340400', '57191771068', '7201537017', '8330197200', '22984888500', '6603265242', '11539314500', '14322959500', '6507207880', '55922688600', '35261977100', '25226148400', '7003389657', '57192213014', '35068969700', '56232933600', '54389741600', '35088976100', '6701448011', '23100119700', '55821080500', '55453849700', '15028126900', '55171306200', '55977064600', '7006591871', '55509921200', '55897704100', '55663794100', '56572349200', '6603213552', '35079669400', '7004089422', '57201213068', '57199533429', '7101751037', '57193387450', '6506740005', '6602438630', '15043266900', '16174915100', '6602346898', '44561349700', '6504162163', '39062085600', '57199626842', '6507602418', '7004113789', '37037044100', '6603547610', '16044227000', '7005401925', '7003687586', '8450623200', '8410918100', '6603612654', '6603671627', '24489601000', '6506915746', '35329630200', '56982473800', '56382536900', '57199671449', '55534141586', '9239479800', '6508295172', '9244245600', '25652237200', '7401452865', '55436007900', '54895523700', '56011876000', '56397875600', '7003716117', '50161027400', '57196748486', '6602190453', '55642412300', '7801550050', '15048854200', '57199560628', '8838928300', '6602655357', '55213605600', '6508097042', '6603457807', '7005169597', '35285914900', '6603495766', '56050550600', '55746242200', '6506794475', '14033052300', '56533905100', '57053331300', '56284194700', '55467553500', '6508337562', '55425546700', '57193314213', '35508748400', '36081401800', '55778498700', '55443485800', '55091075100', '57190677386', '16067143900', '26323750200', '22955020700', '6701373366', '6701877177', '7003736022', '55513986800', '35121960200', '26040840200', '7006195000', '8866775900', '7202434053', '57196937310', '24436285400', '35494145900', '6602992024', '6507756885', '35305970600', '54787068100', '53877170600', '57188638505', '23092351100', '7004703252', '6505540825', '8593427300', '57062013700', '26032561400', '37079930800', '6602978327', '36779634500', '6602569424', '55258444800', '35432038900', '7004102378', '6603557029', '55234999800', '55200515000', '24333653600', '56396838700', '6504523176', '6504528890', '6506521155', '30867495400', '7003780379', '6701448481', '35339764100', '6506000911', '55888067200', '57196836936', '55675566000', '24166120100', '55207356500', '42262646500', '8405982000', '35980129800', '57197619719', '6602925214', '15919469200', '23970246400', '56684332300', '7004524412', '38560911300', '57200309386', '8625448500', '23036982300', '36457373900', '7004242933', '57199354203', '55212163100', '6701409473', '6603190359', '7006702150', '13404650900', '55433385600', '6603385442', '6603440546', '6603268217', '15044164700', '36611561900', '57035632400', '57190401097', '56625710400', '7202566278', '57198451465', '55804938200', '6506945352', '24544394500', '56600591100', '35949013800', '35191711800', '54890646900', '57196003279', '7801619261', '6507520114', '37101173200', '35765914900', '15051301500', '56372460600', '7005738679', '6506889693', '6603215011', '26031214900', '38362041900', '24722713700', '56810863700', '57193970906', '8510789800', '36151530400', '38561024900', '7004182922', '36447805200', '37079296500', '56097196000', '6701413783', '55657159400', '14323306700', '35487103700', '35208353600', '35108699000', '7004002025', '9844120300', '6601956793', '9843652800', '7103138853', '26535125500', '6506902582', '54399316800', '35311447300', '7005573368', '7006073904', '57192586684', '57196681957', '8714970200', '8369761400', '55934469500', '56442669000', '55512689000', '56181386100', '56000233900', '7004711042', '6602132767', '16444111400', '26642932700', '6506132929', '7201991795', '24723069900', '7005926519', '56738854700', '7004333305', '16029978800', '7004217958', '14021658900', '14020140100', '7101856217', '57199338286', '57189327720', '57192707624', '56405314000', '36624468500', '6603420568', '6506884766', '6506456125', '44062229400', '36243622300', '6603828815', '12787360100', '6603980594', '26041126500', '57034735200', '6506689279', '55794733800', '6602820999', '9133252000', '16647162100', '56128868500', '24729442100', '7103077073', '6602793981', '6603346861', '57200185967', '55200047200', '7005102605', '55185187200', '24829625200', '6602305048', '36052311400', '56899767300', '56290725500', '36640833700', '55892094300', '6602876157', '37060576200', '6602887508', '6603475948', '15827428000', '55344270400', '57197759981', '57113895500', '7004571549', '36089304100', '6701361035', '55140007600', '7801559342', '7005125182', '22234566000', '22934324300', '7004296728', '7007004726', '15076841900', '16171928800', '57199356840', '36641589200', '24776431000', '14523405400', '55711443300', '7006477529', '56704996800', '6507227792', '56043629300', '35786508100', '57086473700', '6506195034', '56594619800', '6701691708', '25121686100', '6701400133', '12445297300', '45662064700', '54583395400', '55780826500', '7006421713', '36725993200', '16231065600', '6701411522', '6701398626', '54412078600', '43161429200', '56251885600', '57192586908', '25926784400', '8977959300', '7402323751', '8605583200', '8930137900', '35091084700', '55358295600', '6507555609', '35619394900', '7004032735', '11239528900', '57200410506', '6603548941', '26642494300', '7003751991', '17433287100', '6603821154', '8966508300', '56669635700', '56580074300', '56619043200', '34976839800', '16403362600', '57200204667', '6603852857', '6602514383', '12766757400', '56704839800', '57196016922', '53984501600', '7006938239', '7005314500', '57196709546', '56174902600', '14007806300', '26321279700', '8367117800', '7801542006', '16315301100', '55227672300', '23993458200', '57082634000', '57194272902', '6506135795', '6603804724', '7003263682', '55258981200', '36154238900', '7006320781', '55455928000', '8372814100', '24390311700', '35172788400', '55935969000', '24167128400', '8504126400', '10839198600', '27867819600', '8448208600', '55191471500', '8607356800', '24463232800', '17346560500', '55927660400', '12783254200', '15821672300', '12042387500', '56519470500', '36977144800', '57188948873', '55547132280', '37057702800', '21734955300', '55296730600', '6507631007', '36459918800', '56147377400', '55483844800', '55448072500', '55694670000', '7004354500', '6602219091', '7801685062', '56083458300', '7005097431', '7004062158', '55549569300', '7005618394', '9846127000', '55547174000', '35798078800', '6603802671', '26428605100', '6507021770', '9841420400', '25930709400', '56978815200', '57196353325', '57197761096', '8736091200', '36675460300', '8754182900', '6602551405', '56528389700', '8560588800', '7004155454', '47361576700', '35559898200', '6602344026', '54944562100', '7005707030', '53983237400', '16403763700', '6602268075', '55607129300', '16156014900', '6602703715', '7102878849', '56299040500', '6603107782', '7005330537', '14054956200', '7004093384', '56149762400', '8573363300', '13612457800', '54888516000', '6506401698', '7202771318', '36716781100', '57197559660', '57191048652', '57197849324', '18634271600', '55152523100', '7202194747', '35618399700', '54956607700', '6602705266', '37089303700', '56413074300', '57194171612', '37002546500', '55887503500', '55675891500', '7005334493', '57191620268', '8606833300', '24480471300', '6506800219', '36494295900', '7003930679', '56113972300', '55897942200', '6602099625', '35750697300', '56996103400', '55307977200', '6701344733', '41862824700', '7006340200', '35263173700', '37095719600', '15839021300', '56304049600', '57194753199', '57189873853', '6701499453', '19639411600', '56236190900', '6602389488', '55846370800', '16067172900', '44961606800', '33768160100', '35519530500', '36622548600', '15846198900', '57197490028', '6602407815', '36016823600', '6603062031', '7006636618', '7101982432', '35497296800', '7201838609', '7005622511', '57190010588', '16426089300', '6701700702', '56291975900', '6602621354', '57200416697', '55940569200', '6506135103', '6504292176', '14046367200', '56022570600', '55597335500', '7004322413', '35277685800', '36617346300', '6602124212', '35371891200', '14631172600', '6507749082', '23104572000', '8869416200', '57192125489', '7201404326', '26035243500', '6602674498', '24824703100', '35072464700', '36773556000', '16508216800', '6602732159', '56850057500', '56162389300', '6602909779', '15062163600', '6602283534', '57192008716', '6602333947', '27170624900', '7005148763', '56690693200', '17433264900', '57192043525', '55353077800', '8982316200', '7004860023', '7006396658', '55821208100', '56084459600', '36495970700', '7003958833', '15836869000', '57201022606', '6507173586', '25229153100', '6602239797', '6602252399', '35111637100', '55676014800', '6506209103', '55520895500', '56074760700', '25926438400', '56452715200', '53063156200', '6602124627', '14019389400', '8648313400', '7006450534', '7004153484', '36992961900', '37035761400', '55637656200', '55901093800', '36926852900', '34771247000', '7003953238', '6504689465', '6603010986', '8592483300', '55649997700', '55660064400', '23397002700', '37095441200', '6602319167', '7006602085', '34880105200', '57153806500', '6507145707', '36476746800', '6602505296', '6603277479', '7406084504', '55581346600', '25652629800', '6507301703', '6602991582', '55666055100', '23006833100', '6603435723', '7006311951', '57197426205', '7801618823', '8247452700', '7004383778', '23988852300', '6603108770', '57190225632', '25653991000', '38562322700', '6602147433', '35122461900', '6506327390', '56604809700', '6701617604', '23052128500', '6507484448', '7005938963', '55014484000', '35085205500', '6602341770', '26633529000', '57193717348', '26649247400', '36741838600', '35310839100', '56642263500', '55915869000', '57197127711', '56037137300', '24504164800', '57197545088', '36100226200', '35339174200', '55818372100', '6507427703', '6507661116', '6602841758', '35146498900', '55785363700', '16400630400', '8764319800', '36171748100', '8754141200', '6603457305', '7801395070', '25960128900', '6507133593', '7801337454', '55774483100', '55579727400', '55496868100', '55040308400', '6603134964', '26041212100', '56029782600', '8637473000', '54401220900', '7004720437', '6506458564', '36009432000', '25938031500', '57197488849', '6603790756', '6508220502', '13006833300', '57191613063', '35546265100', '14631735000', '6602281906', '55556770300', '26868173000', '7402073489', '34868426900', '6602075793', '7201967907', '57189027162', '56044656700', '55821697600', '7005277298', '6701755604', '23989003700', '7801393244', '57196481411', '8935838000', '6506701358', '55932781800', '36651667700', '7004036780', '6602767299', '57193265645', '57196997318', '56728548400', '55955638500', '6506074574', '36180130200', '57192868626', '55617220800', '26649211000', '15043304700', '8286222200', '23979034400', '6603589818', '7003870271', '23667705000', '37360952900', '36238526600', '55315654000', '14421885300', '17342812100', '36137863700', '19640079000', '56052509600', '36027672200', '6602804273', '36494117300', '7202885547', '55165091400', '6603285625', '52365300500', '56022122800', '36494926100', '57189576412', '8258826700', '56277529400', '55739321300', '35753520100', '36802888600', '25923135000', '14063424200', '9842776200', '7201848178', '6701769657', '6507436764', '57199610159', '8139951900', '35311265800', '23667615000', '6701617607', '57190045651', '11439241500', '54882000500', '7006956366', '14124203900', '56574299500', '7101895978', '54080493500', '7006827952', '6504634083', '24462430300', '23767520800', '6602223084', '6507528729', '7005254400', '55666257900', '57196860124', '35273890800', '6507876236', '14014366300', '55325802700', '55173991200', '24923262400', '6505933210', '29967448200', '6603714493', '7102279096', '57190002897', '35080641100', '14050683600', '55857352900', '24529158700', '7102915530', '55214772200', '54386387400', '25222353000', '15062780200', '8709405900', '55995228800', '6602397918', '35344842200', '6603768472', '56971470000', '6701516212', '7003548255', '36503965700', '55258728800', '57189869190', '24448154500', '57190282494', '6602923575', '53870480700', '55901699000', '7402785203', '56012582100', '56305815400', '7404083567', '7003334169', '36183620700', '6602335891', '57194015602', '26868045400', '6603569501', '6602312083', '7101761148', '35316697200', '23096130000', '12041658300', '35759765100', '8573363000', '57193454650', '55961356900', '6602909623', '57196277635', '56379891300', '55542469300', '8602677400', '55927083600', '23029569500', '36967681300', '6602823428', '57197016287', '57199021628', '6602569626', '55145801500', '54399210100', '56025981000', '24300140900', '7004911236', '6603295045', '8510882700', '35118611300', '7003430916', '17435301200', '37762350000', '54402947900', '34875687400', '7405338650', '57192875222', '6601986118', '56797515800', '6602974579', '18437395000', '7101691020', '9745876100', '8932557300', '37121762900', '6701914456', '54784892300', '6602293696', '55933936700', '56497753100', '9843308100', '6701735608', '55483773500', '6603502633', '56938174000', '8732229500', '36988496200', '49161071000', '16309026200', '55523763200', '8068332200', '36129481300', '6602659811', '6507087198', '8293905700', '6508182687', '14219934900', '7003791474', '6603929052', '23470421000', '57190495676', '55948430100', '7006039517', '6507982433', '6508169068', '7102400919', '57191596886', '7003656859', '55894042400', '55258728600', '23071903000', '56524621700', '35323729700', '57197072899', '6602798617', '7402833686', '55918779300', '15729827000', '26538580400', '15020089900', '6602907035', '6506647412', '6603805925', '12752468300', '8588762600', '6508361617', '35466109900', '7007132682', '7005223403', '6701654928', '36058819900', '6508244589', '55796743800', '35069514100', '16068941900', '16942708100', '7003538811', '7004593505', '7801582103', '6701692020', '57198257298', '6603822217', '55530756500', '8683494200', '23768173900', '55811534500', '35558885400', '57194158911', '57197786609', '36196582500', '36937919000', '6603813341', '6603760432', '57127148800', '23011510400', '24077579300', '7005929082', '55993870300', '14016764800', '56816870800', '8337608400', '54416979400', '24779284900', '55253064800', '55605084100', '8509303400', '57132619100', '42861383100', '6603477897', '56187310100', '35227950900', '55250096200', '7003866424', '55658316800', '8670753200', '30567801500', '56354131900', '36090661800', '55617168100', '45561015300', '55902019400', '7102997434', '7004592506', '8952890000', '24178964000', '15135366600', '56217609600', '56140844700', '6701656650', '37082073200', '56025159900', '19338144100', '51663653100', '7005678558', '15063584600', '57199549626', '57192237910', '55882245900', '9846285200', '23980540900', '35198359700', '55887364000', '55301509000', '8728135800', '6603378458', '35278497800', '26029986800', '7102846735', '27167858000', '57191055556', '7102774027']
AUID_list = ['57189215838', '6701314974', '56232982900', '7006730867', '7006508852', '6507841115', '55106078200', '8935838200', '57191910422', '23469229300', '50561829200', '36631516500', '7801353451', '54792915600', '56010018200', '8371581300', '36975080500', '57199344188', '6507947915', '55119858000', '23096910700', '7004999647', '56233863200', '36348293900', '7003731759', '6508288286', '35093805100', '57199599606', '22949992000', '55180112800', '12244407800', '23485325000', '16744708600', '57200304389', '7003737362', '55782590400', '6603022519', '8317813000', '55682540300', '7004024063', '57190073774', '56120665200', '24390847200', '25930547300', '57200605007', '55417257000', '7201964130', '15744815200', '57191915512', '36537108700', '6506376604', '22938985300', '37460951300', '53979418400', '37053671300', '57191041133', '56529757000', '7403350771', '41961884000', '54785436900', '40162564600', '36780553300', '26030730000', '7006709352', '6507847032', '57197699477', '6504719437', '56875220400', '57199354845', '35075917900', '6602003141', '36741527500', '6604056271', '6506534030', '36642936000', '25646146900', '55832174700', '55855362200', '55391121700', '57191474838', '55260191500', '7003959718', '55889587300', '55835103400', '22951320200', '57193737577', '13612668100', '36494118100', '35375512000', '8759615400', '55561647900', '35487580200', '6507847776', '7006483726', '6507310838', '6506060597', '7004009631', '6507100137', '7006756560', '55301455900', '36098142800', '14041249700', '56281253300', '7202330527', '54079713100', '57200309747', '35238214700', '6504362827', '36492024900', '7404438219', '21743340400', '6603265242', '11539314500', '55922688600', '7003389657', '56232933600', '6701448011', '55453849700', '55977064600', '7006591871', '55663794100', '35079669400', '57199533429', '6506740005', '6602438630', '6602346898', '39062085600', '7004113789', '16044227000', '7005401925', '8410918100', '24489601000', '56982473800', '55534141586', '9239479800', '25652237200', '54895523700', '7003716117', '6602190453', '15048854200', '6602655357', '6603457807', '6603495766', '6506794475', '57053331300', '57193314213', '55778498700', '57190677386', '22955020700', '7003736022', '26040840200', '6602992024', '54787068100', '23092351100', '8593427300', '37079930800', '6602569424', '7004102378', '6603557029', '6504523176', '6504528890', '7003780379', '6506000911', '55675566000', '42262646500', '57197619719', '23970246400', '38560911300', '57200309386', '57199354203', '6603190359', '55433385600', '6603268217', '57035632400', '7202566278', '6506945352', '35949013800', '57196003279', '37101173200', '56372460600', '6603215011', '24722713700', '8510789800', '36151530400', '36447805200', '6701413783', '35487103700', '7004002025', '9843652800', '6506902582', '7005573368', '57196681957', '55934469500', '56181386100', '6602132767', '6506132929', '7005926519', '56738854700', '7004217958', '7101856217', '57192707624', '6603420568', '44062229400', '36243622300', '6603980594', '6506689279', '9133252000', '24729442100', '6603346861', '7005102605', '6602305048', '36052311400', '36640833700', '37060576200', '15827428000', '57113895500', '6701361035', '7005125182', '7004296728', '16171928800', '24776431000', '14523405400', '56704996800', '6506195034', '56594619800', '6701400133', '54583395400', '36725993200', '6701398626', '56251885600', '8977959300', '7402323751', '6507555609', '11239528900', '26642494300', '6603821154', '56580074300', '16403362600', '56704839800', '7006938239', '56174902600', '8367117800', '55227672300', '57194272902', '7003263682', '7006320781', '24390311700', '24167128400', '27867819600', '8448208600', '24463232800', '12783254200', '56519470500', '55547132280', '55296730600', '56147377400', '55694670000', '7801685062', '7004062158', '9846127000', '6603802671', '9841420400', '25930709400', '57197761096', '8754182900', '47361576700', '54944562100', '16403763700', '16156014900', '56299040500', '14054956200', '8573363300', '6506401698', '7202771318', '18634271600', '35618399700', '37089303700', '37002546500', '55887503500', '57191620268', '6506800219', '56113972300', '35750697300', '6701344733', '35263173700', '56304049600', '6701499453', '6602389488', '44961606800', '33768160100', '15846198900', '7006636618', '7201838609', '16426089300', '6701700702', '57200416697', '6504292176', '55597335500', '36617346300', '14631172600', '8869416200', '26035243500', '35072464700', '36773556000', '56850057500', '15062163600', '6602333947', '56690693200', '17433264900', '8982316200', '55821208100', '7003958833', '6507173586', '6602252399', '6506209103', '53063156200', '8648313400', '7006450534', '37035761400', '36926852900', '6504689465', '55649997700', '7006602085', '6507145707', '36476746800', '25652629800', '55666055100', '7006311951', '8247452700', '6602147433', '23052128500', '55014484000', '26633529000', '36741838600', '35310839100', '57197127711', '57197545088', '6507661116', '8764319800', '36171748100', '7801395070', '7801337454', '6603134964', '26041212100', '54401220900', '36009432000', '6603790756', '57191613063', '26868173000', '6602075793', '7201967907', '55821697600', '23989003700', '8935838000', '36651667700', '57193265645', '55955638500', '57192868626', '15043304700', '6603589818', '37360952900', '14421885300', '17342812100', '56052509600', '36494117300', '6603285625', '36494926100', '56277529400', '36802888600', '9842776200', '6507436764', '35311265800', '57190045651', '7006956366', '7101895978', '6504634083', '6602223084', '55666257900', '6507876236', '55173991200', '29967448200', '57190002897', '55857352900', '25222353000', '15062780200', '6602397918', '56971470000', '36503965700', '24448154500', '53870480700', '7404083567', '6602335891', '6603569501', '12041658300', '57193454650', '57196277635', '8602677400', '57197016287', '57199021628', '54399210100', '8510882700', '17435301200', '34875687400', '7405338650', '56797515800', '7101691020', '37121762900', '6602293696', '9843308100', '6603502633', '36988496200', '55523763200', '6602659811', '6508182687', '6603929052', '23470421000', '7006039517', '7102400919', '55894042400', '56524621700', '6602798617', '15729827000', '6602907035', '12752468300', '35466109900', '6701654928', '55796743800', '16942708100', '7801582103', '6603822217', '23768173900', '57194158911', '36937919000', '57127148800', '7005929082', '55253064800', '55605084100', '42861383100', '7003866424', '30567801500', '55617168100', '7102997434', '24178964000', '56140844700', '56025159900', '7005678558', '57192237910', '23980540900', '55301509000', '35278497800', '7102774027']
df_scopus = pd.DataFrame(columns=['auid', 'status', 'check'])

for n, AUID in enumerate(AUID_list):

    print (n, AUID)
    
    scopus_person = get_scopus_person(AUID, 'a0ff7557d0c58ceb89469ab5291bfc4d')
    time.sleep(1)
    
    df_scopus.loc[len(df_scopus.index)] = [AUID, scopus_person[0], scopus_person[1]]
    df_scopus.to_csv(os.path.join(file_dir, "scopus_person_data.csv"), encoding='utf-8', index = False)
"""
