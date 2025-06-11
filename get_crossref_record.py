import requests
import json
import pandas as pd
import os, sys
import csv

def get_crossref(DOI):

    crossref_api = "https://api.crossref.org/"
    
    response_crossref = requests.get(crossref_api+'works/'+DOI, headers={'Accept': 'application/json'})

    if response_crossref.status_code == 200:
        json_crossref = response_crossref.json()
    else:
        json_crossref = None
    
    return json_crossref, response_crossref.status_code

class getCrossref():
    
    def __init__(self, DOI):

        if DOI is None:
            self.status = "no doi"
            self.json = self.type = self.publisher = self.licenses = self.created_year = self.created_month = self.created_day = self.print_year = self.print_month = self.print_day = self.online_year = self.online_month = self.online_day = self.issued_year = self.issued_month = self.issued_day = self.issue_year = self.issue_month = self.issue_day = self.indexed_year = self.indexed_month = self.indexed_day = None
            return
        
        json_crossref = get_crossref(DOI)[0]
        self.status = get_crossref(DOI)[1]
        if self.status == 200:
            self.json = json_crossref
            self.type = json_crossref['message']['type']
            self.publisher = json_crossref['message']['publisher']
            self.licenses = self.get_licenses(json_crossref)
            self.created_year = self.get_created_date(json_crossref)[0]
            self.created_month = self.get_created_date(json_crossref)[1]
            self.created_day = self.get_created_date(json_crossref)[2]
            self.print_year = self.get_print_date(json_crossref)[0]
            self.print_month = self.get_print_date(json_crossref)[1]
            self.print_day = self.get_print_date(json_crossref)[2]
            self.online_year = self.get_online_date(json_crossref)[0]
            self.online_month = self.get_online_date(json_crossref)[1]
            self.online_day = self.get_online_date(json_crossref)[2]
            self.issued_year = self.get_issued_date(json_crossref)[0]
            self.issued_month = self.get_issued_date(json_crossref)[1]
            self.issued_day = self.get_issued_date(json_crossref)[2]
            self.issue_year = self.get_issue_date(json_crossref)[0]
            self.issue_month = self.get_issue_date(json_crossref)[1]
            self.issue_day = self.get_issue_date(json_crossref)[2]
            self.indexed_year = self.get_indexed_date(json_crossref)[0]
            self.indexed_month = self.get_indexed_date(json_crossref)[1]
            self.indexed_day = self.get_indexed_date(json_crossref)[2]
        else:
           self.json = self.type = self.publisher = self.licenses = self.created_year = self.created_month = self.created_day = self.print_year = self.print_month = self.print_day = self.online_year = self.online_month = self.online_day = self.issued_year = self.issued_month = self.issued_day = self.issue_year = self.issue_month = self.issue_day = self.indexed_year = self.indexed_month = self.indexed_day = None
        

    def get_licenses(self, json_crossref):

        license_list = []
        if json_crossref != None and 'license' in json_crossref['message']:
            
            for license_ in json_crossref['message']['license']:
                license_url = license_['URL']
                license_version = license_['content-version']
                license_list.append(f"{license_url}|{license_version}")
                                    
        return license_list
    
    def get_created_date(self, json_crossref):
        
        if json_crossref != None and 'created' in json_crossref['message']:
            created_date = json_crossref['message']['created']['date-parts']
            created_year = created_date[0][0]
            if len(created_date[0])>1:
                created_month = created_date[0][1]
            else:
                created_month = None
            if len(created_date[0])>2:
                created_day = created_date[0][2]
            else:
                created_day = None
        else:
            created_year = None
            created_month = None
            created_day = None

        return created_year, created_month, created_day

    def get_print_date(self, json_crossref):
        
        if json_crossref != None and 'published-print' in json_crossref['message']:
            print_date = json_crossref['message']['published-print']['date-parts']
            print_year = print_date[0][0]
            if len(print_date[0])>1:
                print_month = print_date[0][1]
            else:
                print_month = None
            if len(print_date[0])>2:
                print_day = print_date[0][2]
            else:
                print_day = None
        else:
            print_year = None
            print_month = None
            print_day = None

        return print_year, print_month, print_day

    def get_online_date(self, json_crossref):
        
        if json_crossref != None and 'published-online' in json_crossref['message']:
            online_date = json_crossref['message']['published-online']['date-parts']
            online_year = online_date[0][0]
            if len(online_date[0])>1:
                online_month = online_date[0][1]
            else:
                online_month = None
            if len(online_date[0])>2:
                online_day = online_date[0][2]
            else:
                online_day = None
        else:
            online_year = None
            online_month = None
            online_day = None

        return online_year, online_month, online_day

    def get_issued_date(self, json_crossref):
        
        if json_crossref != None and 'issued' in json_crossref['message']:
            issue_date = json_crossref['message']['issued']['date-parts']
            issue_year = issue_date[0][0]
            if len(issue_date[0])>1:
                issue_month = issue_date[0][1]
            else:
                issue_month = None
            if len(issue_date[0])>2:
                issue_day = issue_date[0][2]
            else:
                issue_day = None
        else:
            issue_year = None
            issue_month = None
            issue_day = None

        return issue_year, issue_month, issue_day

    def get_issue_date(self, json_crossref):
        
        if json_crossref != None and 'journal-issue' in json_crossref['message']:
            if 'published-print' in json_crossref['message']['journal-issue']:
                issue_date = json_crossref['message']['journal-issue']['published-print']['date-parts']
                issue_year = issue_date[0][0]
                if len(issue_date[0])>1:
                    issue_month = issue_date[0][1]
                else:
                    issue_month = None
                if len(issue_date[0])>2:
                    issue_day = issue_date[0][2]
                else:
                    issue_day = None
            elif 'published-online' in json_crossref['message']['journal-issue']:
                issue_date = json_crossref['message']['journal-issue']['published-online']['date-parts']
                issue_year = issue_date[0][0]
                if len(issue_date[0])>1:
                    issue_month = issue_date[0][1]
                else:
                    issue_month = None
                if len(issue_date[0])>2:
                    issue_day = issue_date[0][2]
                else:
                    issue_day = None
            else:
                issue_year = None
                issue_month = None
                issue_day = None
        else:
            issue_year = None
            issue_month = None
            issue_day = None

        return issue_year, issue_month, issue_day

    def get_indexed_date(self, json_crossref):
        
        if json_crossref != None and 'indexed' in json_crossref['message']:
            indexed_date = json_crossref['message']['indexed']['date-parts']
            indexed_year = indexed_date[0][0]
            if len(indexed_date[0])>1:
                indexed_month = indexed_date[0][1]
            else:
                indexed_month = None
            if len(indexed_date[0])>2:
                indexed_day = indexed_date[0][2]
            else:
                indexed_day = None
        else:
            indexed_year = None
            indexed_month = None
            indexed_day = None

        return indexed_year, indexed_month, indexed_day



"""
#try it out
file_dir = sys.path[0]

#DOI_list = ['10.48550/arXiv.2405.08779', '10.7717/peerj.4375', '10.1007/978-3-031-64892-2_2', '10.1109/BioRob60516.2024.10719815', '10.1017/qua.2024.13']
DOI_list = ['10.48550/arXiv.2405.08779', '10.1007/978-3-031-64892-2_2', '10.1109/BioRob60516.2024.10719815', '10.1017/qua.2024.13', '10.1109/RO-MAN60168.2024.10731262', '10.1109/RO-MAN60168.2024.10731455', '10.1016/j.scitotenv.2024.177570', '10.1111/eth.13504', '10.1002/wcc.901', '10.1109/RO-MAN60168.2024.10731139', '10.5588/ijtld.24.0338', '10.1007/s13755-024-00309-3', '10.1007/978-3-031-64892-2_28', '10.1111/pce.14842', '10.1152/jn.00271.2024', '10.1109/BioRob60516.2024.10719735', '10.1109/ISCC61673.2024.10733725', '10.1016/bs.atpp.2024.09.009', '10.1123/japa.2022-0249', '10.1016/j.tiv.2024.105954', '10.1145/3634737.3637660', '10.1038/s41588-024-01951-z', '10.1302/0301-620X.106B11.BJJ-2024-0264.R1', '10.1007/978-3-031-61976-2_2', '10.1080/02640414.2024.2403285', '10.1093/oso/9780198870319', '10.1016/j.tins.2024.09.011', '10.1109/CASE59546.2024.10711291', '10.1016/j.bbrc.2024.150910', '10.5553/Bw/016571942024078003004', '10.1097/PHM.0000000000002584', '10.1007/978-3-030-61969-5_1', '10.4337/9781803927268.00016', '10.1109/ICECET61485.2024.10698145', '10.1016/j.precamres.2024.107590', '10.1126/science.adl5889', '10.1353/mgs.2024.a937514', '10.1016/j.tics.2024.10.010', '10.1109/TAFFC.2024.3374875', '10.1145/3677045.3685455', '10.1038/s41593-024-01711-6', '10.1016/j.cels.2024.09.010', '10.1109/CVPRW63382.2024.00062', '10.1007/978-3-031-62135-2_28', '10.1038/s43587-024-00683-3', '10.1007/s11187-023-00850-7', '10.1016/j.leaqua.2024.101812', '10.1176/appi.ajp.20231055', '10.1016/s0140-6736(23)02641-7', '10.1163/22117954-bja10104', '10.1053/j.gastro.2024.06.017', '10.1016/j.reprotox.2024.108726', '10.4337/9781800377998.ch24', '10.1080/13600869.2024.2324533', '10.1017/S0033291724001880', '10.1038/s41593-024-01747-8', '10.1007/978-3-031-70239-6_14', '10.1163/15743012-bja10072', '10.1007/978-3-031-70055-2_23', '10.1007/s00186-024-00876-x', '10.1007/978-3-031-70071-2_25', '10.1145/3661455.3669897', '10.1177/17585732241232889', '10.1002/joom.1332', '10.1007/978-3-031-70932-6_16', '10.1007/978-3-031-70932-6_8', '10.5465/amle.2024.0338', '10.1016/j.quascirev.2024.108980', '10.1016/j.ejmech.2024.116693', '10.4337/9781800883130.00017', '10.1093/oso/9780198896388.003.0011', '10.1016/j.watres.2024.122462', '10.1007/978-3-031-70245-7_13', '10.1007/978-3-031-70245-7_12', '10.1109/SP54263.2024.00158', '10.1353/swh.2024.a936678', '10.1523/JNEUROSCI.2096-23.2024', '10.1021/acs.est.4c03123', '10.1007/s11159-024-10108-3', '10.1007/978-3-031-70797-1_27', '10.1037/emo0001340', '10.2308/TAR-2021-0298', '10.1109/ICSA-C63560.2024.00045', '10.1016/j.chemosphere.2024.143319', '10.1504/IJTTC.2024.10066715', '10.1080/1554480x.2024.2381932', '10.1016/j.jelekin.2024.102932', '10.1007/978-3-031-46030-2_11', '10.1111/1365-2745.14388', '10.1145/3573074.3573092', '10.1016/j.chemosphere.2024.143125', '10.1109/REW61692.2024.00022', '10.1109/ICSA-C63560.2024.00070', '10.1152/ajpregu.00036.2024', '10.1038/s41562-024-01852-5', '10.1016/j.jdeveco.2024.103352', '10.1287/mnsc.2023.4909', '10.1016/j.nima.2024.169806', '10.1109/ICMLCN59089.2024.10624805', '10.1287/orsc.2021.14865']

df_crossref = pd.DataFrame(columns=['status-code', 'doi', 'type', 'publisher', 'license-list', 'created_pub_year', 'created_pub_month', 'created_pub_day', 'print_pub_year', 'print_pub_month', 'print_pub_day', 'online_pub_year', 'online_pub_month', 'online_pub_day', 'issued_pub_year', 'issued_pub_month', 'issued_pub_day', 'issue_pub_year', 'issue_pub_month', 'issue_pub_day', 'indexed_year', 'indexed_month', 'indexed_day'])

for n, DOI in enumerate(DOI_list):

    print (n, DOI)
    
    crossref = getCrossref(DOI)

    print (crossref.json)
    
    df_crossref.loc[len(df_crossref.index)] = [crossref.status, DOI, crossref.type, crossref.publisher, crossref.licenses, crossref.created_year, crossref.created_month, crossref.created_day, crossref.print_year, crossref.print_month, crossref.print_day, crossref.online_year, crossref.online_month, crossref.online_day, crossref.issued_year, crossref.issued_month, crossref.issued_day, crossref.issue_year, crossref.issue_month, crossref.issue_day, crossref.indexed_year, crossref.indexed_month, crossref.indexed_day]
    df_crossref.to_csv(os.path.join(file_dir, "crossref_data.csv"), encoding='utf-8', index = False)
"""

