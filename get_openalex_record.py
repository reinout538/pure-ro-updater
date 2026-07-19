import requests
import json
import pandas as pd
import os, sys
import csv
import datetime
"""
def get_openalex(DOI):

    openalex_api = 'https://api.openalex.org/'

    try:    
        response_openalex = requests.get(openalex_api+'works/https://doi.org/'+DOI, headers={'Accept': 'application/json', 'User-Agent': 'mailto:r.dam@vu.nl'})
    except requests.exceptions.RequestException as e:
        json_openalex = None
        print (e)
        return e
    
    if response_openalex.status_code == 200:
        json_openalex = response_openalex.json()        
    else:
        json_openalex = None
    
    return (json_openalex, response_openalex.status_code)
"""
def get_openalex(DOI, max_retries=5):
    
    url = 'https://api.openalex.org/works/https://doi.org/'+DOI
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers={'Accept': 'application/json', 'User-Agent': 'mailto:r.dam@vu.nl'}, timeout=30)
            #print (response.status_code)
            if response.status_code == 200:
                json_openalex = response.json()        
                return (json_openalex, response.status_code)

            if response.status_code == 429:
                # Rate limited - wait longer
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue

            if response.status_code >= 500:
                # Server error - retry
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue

            # Client error - don't retry
            json_openalex = None
            return (json_openalex, response_openalex.status_code)

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

    raise Exception(f"Failed after {max_retries} retries")
    json_openalex = None
    return (json_openalex, response.status_code)

class getOpenalex():
    
    def __init__(self, DOI):

        if DOI is None:
            self.status = "no doi"
            self.set_all_none()
            return
        
        json_openalex = get_openalex(DOI)[0]
        self.status = get_openalex(DOI)[1]
        
        if json_openalex != None:
            self.id = json_openalex['id'].removeprefix("https://openalex.org/")
            self.doi = json_openalex['doi']

            self.pub_year = json_openalex['publication_year']
            self.pub_date = json_openalex['publication_date']
            self.pub_month = json_openalex['publication_date'][5:7]
            self.pub_day = json_openalex['publication_date'][8:10]
            self.main_title = self.get_title(json_openalex)[0]
            self.sub_title = self.get_title(json_openalex)[1]

            #self.authorships = self.get_authorships(json_openalex)
            self.vu_pub = self.get_authorships(json_openalex)

            self.oa_status = json_openalex['open_access']['oa_status']
                        
            self.prim_loc_landing = json_openalex['primary_location']['landing_page_url']
            self.prim_loc_pdf = json_openalex['primary_location']['pdf_url']
            self.prim_loc_is_oa = json_openalex['primary_location']['is_oa']
            self.prim_loc_in_doaj = self.in_doaj(json_openalex)
            self.prim_loc_license = json_openalex['primary_location']['license']
            self.prim_loc_version = json_openalex['primary_location']['version']

            self.green_url_landing = self.get_green_url(json_openalex)[0]
            self.green_url_license = self.get_green_url(json_openalex)[1]
            
            self.vor_pdf_url = self.get_vor_pdf(json_openalex)[0]
            self.vor_pdf_license = self.get_vor_pdf(json_openalex)[1]

            self.pmc_loc_landing = self.get_pmc_loc(json_openalex)[0]
            self.pmc_loc_pdf = self.get_pmc_loc(json_openalex)[1]
            self.pmc_loc_is_oa = self.get_pmc_loc(json_openalex)[2]
            self.pmc_loc_license = self.get_pmc_loc(json_openalex)[3]
            self.pmc_loc_version = self.get_pmc_loc(json_openalex)[4]

            self.journal = self.get_journal_title(json_openalex)[0]
            self.issn = self.get_journal_title(json_openalex)[1]

            self.volume = json_openalex['biblio']['volume']
            self.issue = json_openalex['biblio']['issue']
            self.first_page = json_openalex['biblio']['first_page']
            self.last_page = json_openalex['biblio']['last_page']

        else:
            self.set_all_none()
                
    
    def set_all_none(self):
        # Helper function to initialize all attributes to None
        self.id = self.doi = self.pub_year = self.pub_date = self.pub_month = self.pub_day = self.main_title = self.sub_title = self.vu_pub = self.oa_status = self.prim_loc_landing = self.prim_loc_pdf = self.prim_loc_is_oa = self.prim_loc_in_doaj = self.prim_loc_license = self.prim_loc_version = self.green_url_landing = self.green_url_license = self.vor_pdf_url = self.vor_pdf_license = self.pmc_loc_landing = self.pmc_loc_pdf = self.pmc_loc_is_oa = self.pmc_loc_license = self.pmc_loc_version = self.journal = self.issn = self.volume = self.issue = self.first_page = self.last_page = None
    
    def get_title(self, json_openalex):
        
        if json_openalex['title'] != None:
            full_title = json_openalex['title']   
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

    def get_journal_title (self, json_openalex):

        if json_openalex['primary_location']['source'] != None:
            if json_openalex['primary_location']['source']['type'] == 'journal':
                journal_title = json_openalex['primary_location']['source']['display_name']
                if 'issn_l' in json_openalex['primary_location']['source']:
                    journal_issn = json_openalex['primary_location']['source']['issn_l']
                else:
                    journal_issn = None
            else:
                journal_title = None
                journal_issn = None
        else:
            journal_title = None
            journal_issn = None
                
        return journal_title, journal_issn

    def get_authorships (self, json_openalex):
        #work in progress
        vu_pub = False
        
        for authorship in json_openalex['authorships']:
            #print (authorship['author_position'])
            #print (authorship['author'].get('id'))
            #print (authorship['author'].get('display_name'))
            #print (authorship['author'].get('orcid'))
            for institution in authorship['institutions']:
                #print (institution['id'])
                #print (institution['ror'])
                #print (institution['display_name'])
                if institution['ror'] == "https://ror.org/008xxew50":
                    vu_pub = True
            for affil in authorship['affiliations']:
                pass
                #print (affil['raw_affiliation_string'])
                #print (affil['institution_ids'])
        
        return vu_pub

    def in_doaj (self, json_openalex):

        if json_openalex['primary_location']['source'] != None:
            in_doaj = json_openalex['primary_location']['source']['is_in_doaj']
        else:
            in_doaj = None

        return in_doaj
        
    def get_green_url (self, json_openalex):
        
        loc_land = loc_license = None
        candidates = []
        excluded = ['research.vu.nl', 'doaj', 'pmc', '1871']

        for loc in json_openalex['locations']:
            
            if loc['is_oa'] == True and loc['landing_page_url'] != None and loc['version'] != 'publishedVersion':
                if any(excl in loc['landing_page_url'] for excl in excluded):
                    continue
                else:
                    candidates.append(loc)
            else:
                continue
            
        for candidate in candidates:
            loc_land = candidate['landing_page_url']
            loc_license = candidate['license']

            #quit if handle or urn url found
            if ('handle.net' or 'urn.') in candidate['landing_page_url'] and not 'handle.net/1871' in ['landing_page_url']:
                break
        
        return loc_land, loc_license


    def get_vor_pdf (self, json_openalex):
        
        loc_pdf = loc_license = None
        
        for loc in json_openalex['locations']:
            if loc['version'] == 'publishedVersion' and loc['pdf_url'] != None:
                loc_pdf = loc['pdf_url']
                loc_license = loc['license']
                break
            else:
                continue
                        
        return loc_pdf, loc_license
    
    def get_pmc_loc (self, json_openalex):
        
        loc_land = loc_pdf = loc_oa = loc_license = loc_version = None

        for loc in json_openalex['locations']:
            
            if loc['source'] != None:
                if loc['source']['id'] == 'https://openalex.org/S2764455111' and 'pmc' in loc['landing_page_url']:
                    loc_land = loc['landing_page_url']
                    loc_pdf = loc['pdf_url']
                    loc_oa = loc['is_oa']
                    loc_license = loc['license']
                    loc_version = loc['version']
                else:
                    continue
            else: continue
            
        return loc_land, loc_pdf, loc_oa, loc_license, loc_version
    

"""
#try it out
from download_pdf import *
file_dir = sys.path[0]
DOI_list = ['10.1080/16549716.2024.2403972', '10.1103/PhysRevLett.133.261804', '10.1177/10888683241302247', '10.1007/s12117-024-09556-y', '10.20495/seas.13.3_487', '10.1021/acs.jpclett.4c03126', '10.1073/pnas.2412355121', '10.1016/j.tcs.2024.114875', '10.1016/j.isci.2024.111410', '10.1016/j.scitotenv.2024.177570', '10.1103/PhysRevLett.133.251801', '10.1021/acsphotonics.4c01451', '10.1021/acsphotonics.4c01737', '10.1016/j.bbrc.2024.150910', '10.1002/ejoc.202400870', '10.1016/j.saa.2024.124868', '10.1016/j.pecinn.2024.100341', '10.1016/j.pecinn.2024.100331', '10.1016/j.pecinn.2024.100337', '10.1108/CDI-03-2024-0096', '10.1021/acs.jchemed.4c00875', '10.1073/pnas.2407644121', '10.1080/13691457.2024.2436029', '10.1126/sciadv.adq1383', '10.1108/JOE-04-2024-0018', '10.1073/pnas.2413433121', '10.3390/jcm13247571', '10.1002/ejoc.202400797', '10.1063/5.0247819', '10.3390/jcm13247512', '10.1016/j.watres.2024.122462', '10.1016/j.aca.2024.343287', '10.1175/BAMS-D-24-0145.1', '10.1364/PRJ.533983', '10.1016/j.scitotenv.2024.176431', '10.1177/25158163241235574', '10.1007/s00223-024-01305-1', '10.1016/j.cie.2024.110651', '10.1016/j.cogsys.2024.101280', '10.1186/s12875-024-02680-2', '10.1038/s41598-024-73963-y', '10.1038/s41597-024-03864-2', '10.1016/j.gr.2024.07.025', '10.1088/2752-5295/ad9f8f', '10.1002/alz.088963', '10.1016/j.cogsys.2024.101288', '10.1016/j.cogsys.2024.101290', '10.1016/j.jhg.2024.07.012', '10.1007/s40520-024-02798-4', '10.1016/j.iotech.2024.100724', '10.1038/s41467-024-52728-1', '10.3847/1538-4357/ad8de0', '10.1063/5.0220970', '10.1111/cdoe.12987', '10.1002/alz.088662', '10.1038/s41598-024-72661-z', '10.1016/j.oooo.2024.07.003', '10.1002/alz.088788', '10.1007/s11571-023-09987-3', '10.1002/alz.14272', '10.1038/s41467-024-53256-8', '10.1139/bcb-2024-0100', '10.5334/ijic.8588', '10.1002/alz.092165', '10.1177/20503121241272636', '10.1016/j.preghy.2024.101171', '10.1002/alz.086452', '10.1177/14687984221082240', '10.1016/j.ecolecon.2024.108352', '10.1016/j.jelekin.2024.102910', '10.1186/s13059-024-03427-z', '10.1016/j.ejrh.2024.102090', '10.1111/aogs.14947', '10.1038/s41386-024-02023-w', '10.2519/jospt.2024.12735', '10.1017/S0268416025000049', '10.1186/s40163-024-00231-9', '10.4067/S0717-92002024000300485', '10.1016/j.ssmmh.2024.100366', '10.1186/s12913-024-11586-9', '10.1136/bmjopen-2024-087939', '10.1016/j.phanu.2024.100420', '10.1007/s43615-024-00379-1', '10.1186/s12888-024-06372-0', '10.1016/j.copsyc.2024.101913', '10.1177/20494637241263291', '10.1177/03795721241293547', '10.1111/gcb.17590', '10.1016/j.invent.2024.100787', '10.1287/deca.2023.0138', '10.1002/alz.090660', '10.1002/alz.092202', '10.3390/epigenomes8040037', '10.1016/j.cogsys.2024.101282', '10.1016/j.tfp.2024.100717', '10.1103/PhysRevA.110.062813', '10.5751/ES-15486-290424', '10.1016/j.tim.2024.10.004', '10.1016/j.chbr.2024.100508', '10.1111/issr.12374', '10.3390/ijms252413700', '10.3390/laws13060073', '10.1016/j.techfore.2024.123779', '10.1016/j.copbio.2024.103195', '10.1111/1365-2745.14422', '10.1038/s43247-024-01934-2', '10.5585/2024.27115', '10.1007/s10995-024-03986-4', '10.1038/s41558-024-02176-y', '10.1016/j.copsyc.2024.101897', '10.1127/nos/2024/0817', '10.3390/rs16244744', '10.1186/s12913-024-11704-7', '10.3390/biomedicines12122913', '10.1007/s11325-024-03162-6', '10.1016/j.apjon.2024.100615', '10.1037/pne0000345', '10.1177/08862605241246800', '10.1007/s13755-024-00309-3', '10.1016/j.psyneuen.2024.107190', '10.1007/s12286-024-00617-8', '10.1016/j.gloenvcha.2024.102940', '10.1016/j.soilbio.2024.109602', '10.1016/j.ssmph.2024.101712', '10.1088/1748-9326/ad948c', '10.1007/JHEP12(2024)026', '10.1038/s41598-024-81373-3', '10.1016/j.ejrad.2024.111721', '10.1016/j.reprotox.2024.108726', '10.1007/s10479-024-06265-1', '10.1002/alz.087304', '10.1088/1748-9326/ad80af', '10.1002/jcsm.13608', '10.1007/s40865-025-00268-7', '10.1186/s12874-024-02419-8', '10.1111/scd.13042', '10.1016/j.joca.2024.07.007', '10.55563/clinexprheumatol/gymjl1', '10.1007/s11007-024-09663-1', '10.1016/j.soilbio.2024.109604', '10.1016/j.vacuum.2024.113708', '10.1186/s40345-024-00360-9', '10.1093/toxsci/kfae131', '10.1038/s41612-024-00779-y', '10.1016/j.jeconom.2024.105894', '10.1038/s41588-024-02047-4', '10.1038/s41386-024-01940-0', '10.1186/s12302-024-00987-6', '10.1111/ppl.70008', '10.1016/j.ecolecon.2024.108324', '10.1088/2516-1075/ad48ec', '10.1007/s11571-023-09979-3', '10.1103/PhysRevA.110.062804', '10.1016/j.jrp.2024.104529', '10.9745/GHSP-D-23-00381', '10.1111/obes.12628', '10.1088/1748-9326/ad8f48', '10.1007/s10676-024-09804-3', '10.1007/s10458-024-09676-3', '10.1111/joop.12514', '10.1007/s11120-023-01048-4', '10.1007/s10790-022-09916-3', '10.1017/S003329172400299X', '10.1007/s10728-023-00469-5', '10.1090/proc/17018', '10.1038/s41467-024-53645-z', '10.1128/aac.01232-24', '10.1111/joor.13852', '10.1186/s12888-024-06420-9', '10.1007/s00431-024-05815-w', '10.1093/heapol/czae079', '10.1111/tme.13108', '10.1111/sjop.13059', '10.1016/j.brs.2024.10.008', '10.15388/infedu.2024.28', '10.3390/ijns10040070', '10.3390/f15122092', '10.1038/s41467-024-52926-x', '10.1016/j.jrt.2024.100100', '10.3390/land13121973', '10.1016/j.eist.2024.100921', '10.1016/j.jbusres.2024.114912', '10.1159/000540554', '10.1186/s40359-024-02298-0', '10.1097/01.ogx.0001096628.20589.10', '10.5465/amle.2024.0445', '10.1016/j.jcrimjus.2024.102276', '10.1111/mec.17538', '10.1016/j.endeavour.2024.100967', '10.1096/fj.202302258R', '10.1002/anie.202409528', '10.1002/adhm.202400750', '10.1088/1751-8121/ad8a2a', '10.26493/2590-9770.1577.7ca', '10.1016/j.cels.2024.10.009', '10.1080/19415257.2024.2426506', '10.1021/acs.est.4c03868', '10.1073/pnas.2406061121', '10.1016/j.scitotenv.2024.175361', '10.1016/j.quascirev.2024.108980', '10.1016/j.neucom.2024.128396', '10.1021/acs.est.4c04512', '10.1073/pnas.2221623121', '10.1016/j.jhazmat.2024.135592', '10.1364/OE.539655', '10.1144/jgs2023-110', '10.3390/jcm13226891', '10.3390/ijms252212430']
DOI_list = ["10.1016/j.physletb.2017.01.044"]

df_openalex = pd.DataFrame(columns=['openalex.id', 'doi', 'pub_year', 'pub_date', 'pub_month', 'pub_day', 'main_title', 'sub_title', 'vu_pub', 'oa_status', 'prim_loc_landing', 'prim_loc_pdf', 'pdf_status', 'prim_loc_is_oa', 'prim_loc_in_doaj', 'prim_loc_license', 'prim_loc_version', 'green_url_landing', 'green_url_license', 'vor_pdf_url', 'vor_pdf_license' ,'pmc_loc_landing', 'pmc_loc_pdf', 'pmc_loc_is_oa', 'pmc_loc_license', 'pmc_loc_version', 'journal', 'issn', 'volume', 'issue', 'first_page', 'last_page'])

#create session log directory
path_session_add = 0
path_session = os.path.join(file_dir, 'openalex_output', str(datetime.datetime.now().strftime('%Y-%m-%d')))
while os.path.exists(path_session) == True:
    path_session_add += 1
    path_session = f"{os.path.join(file_dir, 'openalex_output', str(datetime.datetime.now().strftime('%Y-%m-%d')))}_{str(path_session_add)}"
os.makedirs (path_session)

for n, DOI in enumerate(DOI_list[0:]):

    print (f"{n+1} of {len(DOI_list)}", DOI)
    
    openalex = getOpenalex(DOI)
    
    if openalex.prim_loc_pdf:
        pdf_status = save_openalex_pdf (openalex.prim_loc_pdf, DOI, path_session)
    else:
        pdf_status = "none"

    print (openalex.status)    

    df_openalex.loc[len(df_openalex.index)] = [openalex.id, openalex.doi, openalex.pub_year, openalex.pub_date, openalex.pub_month, openalex.pub_day, openalex.main_title, openalex.sub_title, openalex.vu_pub, openalex.oa_status, openalex.prim_loc_landing, openalex.prim_loc_pdf, pdf_status, openalex.prim_loc_is_oa, openalex.prim_loc_in_doaj, openalex.prim_loc_license, openalex.prim_loc_version, openalex.green_url_landing, openalex.green_url_license, openalex.vor_pdf_url, openalex.vor_pdf_license, openalex.pmc_loc_landing, openalex.pmc_loc_pdf, openalex.pmc_loc_is_oa, openalex.pmc_loc_license, openalex.pmc_loc_version, openalex.journal, openalex.issn, openalex.volume, openalex.issue, openalex.first_page, openalex.last_page]
    df_openalex.to_csv(os.path.join(file_dir, path_session, "openalex_data.csv"), encoding='utf-8', index = False)

"""
