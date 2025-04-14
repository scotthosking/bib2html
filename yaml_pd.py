import pandas as pd
import yaml
import numpy as np
from datetime import datetime 
from bs4 import BeautifulSoup
import urllib.request


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--short_version")
args = parser.parse_args()


if args.short_version == 'True':
    print("full_author_info = True")
    full_author_info = True

if args.short_version == 'False':
    print("full_author_info = False")
    full_author_info = False


'''
To do:
* Shorten journal titles if desired, e.g., "J. Clim"
* Use initials for names only, but keep e.g., J.-F. (see Amos et al)
'''

if full_author_info:
    outfile = 'publications.html'
else:
    outfile = 'publications_short.html'


with open('jsh_bib.yaml', 'r') as f:
    raw = pd.json_normalize(yaml.load(f, Loader=yaml.FullLoader))

n = raw.shape[1]

'''
Extract all columns required to build DataFrame
'''
columns = []
for i in range(0,n):
    key = raw.iloc[:,i].name
    columns.append(key.split('.')[-1])

columns = np.unique(columns)


'''
Loop through data and fill DataFrame with values
'''
df_all = pd.DataFrame([])
df     = pd.DataFrame(columns=columns)
last_paper_id = '-1'



def author_dict2str(value, full_author_info=True):

    author_list = []
    et_al_position = len(value)

    for j in range(0,len(value)):

        dict = value[j]

        fst_name = dict['first']
        lst_name = dict['last']

        if '-' not in fst_name:
            fst_name = fst_name[0]+'.'
        else:
            splt = fst_name.split('-')
            fst_name = splt[0][0]+'.-'+splt[1][0]+'.'
            
        if 'middle' in dict.keys():
            mid_name = dict['middle']
            fst_name = fst_name+' '+mid_name[0]+'.' 

        if full_author_info == True:
            ### construct name with initials
            author = fst_name + ' ' + lst_name
        else:
            ### construct name with only surname
            author = lst_name

        ### find me! make bold and remember position in list
        if (lst_name == 'Hosking') | (lst_name == 'Hosking!'): 
            et_al_position = j
            if author.endswith('!'): 
                author = '<b>'+author[:-1]+'</b>!'
            else:
                author = '<b>'+author+'</b>'

        author_list.append(author)

    ### join author list together with a comma to separate each author
    author_str = ', '.join(author_list)

    ### Optional: If any authors after 'Hosking', remove them and add 'et al.'
    if (full_author_info is False) & (et_al_position < len(value)-1):
        author_str = ', '.join(author_list[0:et_al_position+1])+' et al.'

    if dict['last'].endswith('!'): author_str = author_str.replace('!', ' et al.')  
    
    ### see: https://www.ou.edu/research/electron/internet/special.shtml
    author_str = author_str.replace(r"\'e", "&eacute;")
    author_str = author_str.replace(r"\`e", "&egrave;")
    author_str = author_str.replace(r'\"o', '&ouml;')
    author_str = author_str.replace(r'\'a', '&aacute;')
    author_str = author_str.replace(r'\o' , '&oslash;')
    
    return author_str
    



for i in range(0,n):

    key      = raw.iloc[:,i].name
    paper_id = key.split('.')[1]
    col      = key.split('.')[-1]
    value    = raw.iloc[:,i].values[0]

    if col == 'author':
        author_str = author_dict2str(value, full_author_info=full_author_info)
        value = author_str

    if paper_id != last_paper_id: # why do we need this? can't remember...
        df_all = pd.concat([df_all,df])
        df     = pd.DataFrame(columns=columns, index=[paper_id])

    df[col]       = value
    last_paper_id = paper_id

df_all = pd.concat([df_all,df])






'''
Google Scholar Scraper
'''

if full_author_info == True:
    url="https://scholar.google.co.uk/citations?user=Z9vzJ2cAAAAJ&hl=en" 
    page = urllib.request.urlopen(url) 
    soup = BeautifulSoup(page, 'html.parser')     

    indexes   = soup.find_all("td", "gsc_rsb_std")                            
    h_index   = indexes[2].string 
    i10_index = indexes[4].string 
    citations = indexes[0].string 


'''
Write html file
'''

with open(outfile, 'w') as file:

    file.write('---\n')
    file.write('layout: page\n')
    file.write('permalink: /'+outfile.split('.')[0]+'\n')
    file.write('title: "Publications"\n')
    file.write('description: 2010 - present\n')
    file.write('excerpt: "J. Scott Hosking - Publications"\n')
    if full_author_info: file.write('nav-menu: true\n')
    file.write('image: assets/images/wwf_spatial_finance.jpg\n')
    file.write('last_modified_at: '+datetime.now().strftime('%Y-%m-%d')+'\n')
    file.write('---\n')

    file.write('<h1><a id="Publications"></a>Publications</h1>\n')

    '''
    Links:
    '''
    scholar_part = '<a href="https://scholar.google.co.uk/citations?user=Z9vzJ2cAAAAJ&hl=en">Google Scholar</a>'
    orcid_part   = '<a href="https://orcid.org/0000-0002-3646-3504">ORCID: 0000-0002-3646-3504</a>'
    scopus_part  = '<a href="https://www.scopus.com/authid/detail.uri?authorId=36449157300">Scopus ID: 36449157300</a>'
    
    if full_author_info == True:
        h_index_part   = 'h-index = '+h_index
        citations_part = 'citations = '+citations
        date_part      = '('+datetime.now().strftime("%B %Y")+')'
        
        file.write( '<sub>' +scholar_part+': '+h_index_part+', '+citations_part+' '+date_part+'</sub>\n')
        # file.write( '<sub>' +orcid_part+ ' | ' +scopus_part+ '</sub>')
        file.write('<br><br>')


    '''
    Preprint:
    '''
    df_preprint = df_all[ df_all['type'] == 'preprint' ]
    if len(df_preprint) > 0:
        file.write('<h3><a id="Preprints"></a>Preprints</h3>\n')
        file.write('<ul>\n')
    for index, row in df_preprint.iterrows():
        author_part  = '<span class="author">'+row['author']+'</span>, '

        if row['doi'] != '':
            url_part     = 'http://dx.doi.org/'+row['doi']
        else:
            url_part     = row['url']

        title_part = '<span class="title"><a href="'+url_part+'">'+row['title']+'</a></span>, '

        journal_part = '<i>'+row['journal']+'</i>'
        line = '<li>'+author_part+title_part+journal_part+'</li>\n'
        file.write(line)
    file.write('</ul>\n')


    # '''
    # e-Prints:
    # '''
    # df_eprints = df_all[ df_all['type'] == 'eprint' ]
    # if len(df_eprints) > 0:
    #     file.write('<h2><a id="e-Prints"></a>e-Prints</h2>\n')
    #     file.write('<ul>\n')
    # for index, row in df_eprints.iterrows():
    #     author_part = '<span class="author">'+row['author']+'</span>'
    #     year_part   = '<span class="year"> ('+row['year']+') </span>'
    #     # title_part  = '<span class="title">"'+row['title']+'"</span>, '
    #     if row['archiveprefix'] == 'arXiv':
    #         title_part = '<a href="https://arxiv.org/abs/'+row['eprint']+'">'+row['title']+'</a>, '
    #     else:
    #         raise ValueError('do not recognise ePrint site')
    #     eprint_part = 'arXiv:'+row['eprint']
    #     line = '<li>'+author_part+year_part+title_part+eprint_part+'</li>\n'
    #     file.write(line)
    # file.write('</ul>\n')


    # '''
    # Conference:
    # '''
    # df_conference = df_all[ df_all['type'] == 'conference' ]
    # file.write('<h2><a id="Conference Publications"></a>Conference Publications</h2>\n')
    # file.write('<ol reversed>\n')
    # for index, row in df_conference.iterrows():
    #     author_part  = '<span class="author">'+row['author']+'</span>'
    #     year_part    = '<span class="year"> ('+row['year']+') </span>'
    #     title_part   = '<span class="title"><a href="'+row['url']+'">"'+row['title']+'"</a></span>, '
    #     booktitle_part = '<i>'+row['booktitle']+'</i>'
    #     line = '<li>'+author_part+year_part+title_part+booktitle_part+'</li>\n'
    #     file.write(line)
    # file.write('</ol>\n')


    '''
    Peer-reviewed:
    '''
    df_articles = df_all[ df_all['type'] == 'article' ]
    file.write('<h3><a id="Peer-reviewed"></a>Peer-reviewed</h3>\n')
    file.write('<ol reversed>\n')
    for index, row in df_articles.iterrows():
        author_part  = '<span class="author">'+row['author']+'</span>'

        author_part= author_part.replace('{','').replace('}','')

        year_part    = '<span class="year"> ('+row['year']+') </span>'

        if row['doi'] != '':
            url_part     = 'http://dx.doi.org/'+row['doi']
        else:
            url_part     = row['url']

        title_part   = '<span class="title">"<a href="'+url_part+'">'+row['title']+'</a>"</span>,'
        journal_part = '<i>'+row['journal']+'</i>'

        # if full_author_info:
        #     if type(row['volume']) == str: journal_part = journal_part + ' Vol. '+row['volume']+','
        #     if type(row['number']) == str: journal_part = journal_part + ' No. '+row['number']+','
        

        try:
            media_tag_split = row['media'].split(';')

            media_tags = '<br>'

            for kk in media_tag_split:
                tag_name,tag_col,tag_url = kk.split(',')
                tag_name = tag_name.strip()
                media_tag = '<small><a href='+tag_url+'> \
                                <span style="padding: 2px; \
                                            padding-left: 8px; padding-right: 8px; \
                                            background: '+tag_col+'; \
                                            border-radius: 10px; \
                                            color: #FFFFFF; \
                                            text-decoration: none; \
                                            white-space: nowrap \
                                            ">' \
                                +tag_name+'</span></a></small>'

                media_tags = media_tags + media_tag
        except:
            media_tags = ''



        if full_author_info:
            line = '<li>'+author_part+year_part+title_part+' '+journal_part+media_tags+'&nbsp;</li>\n'
        else:
            line = '<li>'+author_part+year_part+title_part+' '+journal_part+'</li>\n'



        file.write(line)
    file.write('</ol>\n')

    '''
    Reports:
    '''
    df_techreport = df_all[ df_all['type'] == 'techreport' ]
    file.write('<h2><a id="Reports"></a>Reports</h2>\n')
    file.write('<ul>\n')
    for index, row in df_techreport.iterrows():
        author_part  = '<span class="author">'+row['author']+'</span>'
        year_part    = '<span class="year"> ('+row['year']+') </span>'
        title_part   = '<span class="title"><a href="'+row['pdf']+'">"'+row['title']+'"</a></span>, '
        institution_part = '<i>'+row['institution']+'</i>'
        line = '<li>'+author_part+year_part+title_part+institution_part+'</li>\n'
        file.write(line)
    file.write('</ul>\n')

    '''
    PhD Thesis:
    '''
    df_thesis = df_all[ df_all['type'] == 'phdthesis' ]
    file.write('<h2><a id="PhD Thesis"></a>PhD Thesis</h2>\n')
    file.write('<ul>\n')
    for index, row in df_thesis.iterrows():
        author_part  = '<span class="author">'+row['author']+'</span>'
        year_part    = '<span class="year"> ('+row['year']+') </span>'
        title_part   = ' <a href="'+row['url']+'">'+row['title']+'</a>, '
        school_part  = ''+row['school']
        line = '<li>'+author_part+year_part+title_part+school_part+'</li>\n'
        file.write(line)
    file.write('</ul>\n')

    '''
    Datasets:
    '''
    df_datasets = df_all[ df_all['type'] == 'datasets' ]
    file.write('<h2><a id="Datasets"></a>Datasets</h2>\n')
    file.write('<ul>\n')
    for index, row in df_datasets.iterrows():
        author_part  = '<span class="author">'+row['author']+'</span>, '
        title_part   = ' <a href="'+row['url']+'">'+row['title']+'</a>&nbsp;'
        line = '<li>'+author_part+title_part+'</li>\n'
        file.write(line)
    file.write('</ul>\n')

    file.write( '<br><br> <a href="https://www.nature.com/collections/afchdbedbe"><img src="assets/images/nat_comms_top25.jpg"></a>' )
