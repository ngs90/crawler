import os
import uuid
import glob
import time
import pickle
from bs4 import BeautifulSoup, SoupStrainer
import urllib
import re
from collections import defaultdict
from selenium import webdriver
from urllib.request import urlopen
from webdriver_manager.chrome import ChromeDriverManager  # from webdriver_manager.firefox import GeckoDriverManager

# Helpful links:
# https://stackoverflow.com/questions/29404856/how-can-i-render-javascript-html-to-html-in-python
# https://stackoverflow.com/questions/29858752/error-message-chromedriver-executable-needs-to-be-available-in-the-path

TEMP_DATA_PATH = 'C:/working/ngs-lib/Boligsalg/data/url_data/'

def get_bolig_dict(municipality_code='101', page=1):
    bolig_dict = defaultdict(str)

    url_in_scope = f'https://www.boliga.dk/resultat?sort=zipCode-a&municipality={municipality_code}&page={page}'
    print('Scraping', url_in_scope)
    try:
        page = urllib.request.urlopen(url_in_scope)  # Load that page!

        for link in BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('a')):  # look only for subset "a"

            if link.has_attr('href'):  # Look for links
                # Match the correct link pattern
                if re.match('/bolig/\d*/.*', link['href']):
                    bolig_dict[link['href']] = defaultdict(str)  # Save relative link as dictionary key


    except Exception as e:
        print("An error occured.", e)

    return bolig_dict


def get_html_with_js(url, quit_browser=True, close_tabs=False, browser=None):
    """
    Description:
        Get html based on an url with javascript data compiled
    Input:
        url (str): Url to load and js compiled
    Returns:
        str: html including compiled js content
    """
    file_name = os.path.join(TEMP_DATA_PATH, f'data_{uuid.uuid4()}.txt')

    # Store HTML locally
    conn = urlopen(url)
    data = conn.read()
    conn.close()
    file = open(file_name, 'wb')
    file.write(data)
    file.close()

    # Compile javascript to get complete complete html
    if browser is None:
        browser = webdriver.Chrome(ChromeDriverManager().install())
        # browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    else:
        pass
    browser.get('file:///' + file_name)  # browser.get(url)
    html = browser.page_source
    if quit_browser:
        browser.quit()
    if close_tabs:
        browser.close()  # close_tabs()

    return html


def initialize_lookout_dict():
    """
    Description:
        Set's up the definitions to look for in a html file.

        * start_key: pattern t look for, for start of key ordered
        * start_key: pattern to look for, for start of key ordered.
        * start_value: pattern to look for, for start of value ordered.
        * end_value: pattern to look for, for end of value ordered.
        * name: Predefined name. If false then start_key/end_key needs to be specified
        * list: False results expected to be only on for each key. True if multiple values for each key.
        * limit: limit of iterations to look for the start_value/start_key/end_value/end_key patterns.
    Returns:
        dict: Dictionary desscribing which patterns to look for

    """
    lookout_dict = {}
    lookout_dict['Adresse'] = {'start_value': ['<meta name="keywords" content="">', '<title>'],
                               'end_value': ['</title>', ' - '],
                               'name': 'Adresse',
                               'list': False,
                               'limit': 1}

    lookout_dict['Basisoplysninger'] = {
        'start_key': ['<span _ngcontent-sc', '="" class="mb-1 d-md-none font-weight-bold w-100">'],
        'end_key': ['</span>'],
        'start_value': ['<span _ngcontent-sc', '="" class="d-md-none my-auto">'],
        'end_value': ['</span>'],
        'name': None,  # missing, so will need to find it in data!
        'list': False,
        'limit': 9}

    lookout_dict['Pris'] = {'start_value': ['<span class="h-md-2 h4 font-weight-bold m-0 text-nowrap">'],
                            'end_value': ['</span>'],
                            'name': 'Pris',  # missing, so will need to find it in data!
                            'list': False,
                            'limit': 1}

    lookout_dict['Timeline'] = {
        'start_value': ['class="timeline">', '<span _ngcontent-sc', '="" class="d-sm-none d-table-cell timeline">'],
        'end_value': ['</span>'],
        'name': 'Timeline_time',  # missing, so will need to find it in data!
        'list': True,
        'limit': 10}

    lookout_dict['Timeline_action'] = {
        'start_value': ['class="timeline">', '<div _ngcontent-sc', '="" class="mr-0 mr-sm-2"><!---->'],
        'end_value': ['<!---->'],
        'name': 'Timeline_action',  # missing, so will need to find it in data!
        'list': True,
        'limit': 10}

    lookout_dict['Timeline_price'] = {
        'start_value': ['class="timeline">', 'd-sm-none d-table-cell month', '<span _ngcontent-sc', '="">'],
        'end_value': ['<'],
        'name': 'Timeline_price',  # missing, so will need to find it in data!
        'list': True,
        'limit': 10}

    lookout_dict['Boligtype'] = {
        'start_value': ['<app-tooltip _ngcontent-sc', '=""', ' class="md-right flex-shrink-0" _nghost-sc',
                        '=""><!---->', '<p _ngcontent-sc', '="" class="app-tooltip ng-star-inserted"><!----><!---->'],
        'end_value': ['<!---->'],
        'name': 'Boligtype',  # missing, so will need to find it in data!
        'list': False,
        'limit': 1}

    lookout_dict['Oprettet'] = {
        'start_value': ['BBR', 'BBR-arealet opmåles fra ydersiden af hver ydervæg og indeholder arealer som fx opgang.',
                        '<app-tooltip class="tooltip-nowrap" _nghost-sc', '="">', '<!----><p _ngcontent-sc', '=""',
                        ' class="app-tooltip ng-star-inserted"><!----><!---->', '<p _ngcontent-sc',
                        '="" class="app-tooltip ng-star-inserted"><!----><!---->'],
        'end_value': ['<!---->'],
        'name': 'Oprettet',  # missing, so will need to find it in data!
        'list': False,
        'limit': 1}

    lookout_dict['Markedstid'] = {
        'start_value': ['<use xlink:href="#icon-calendar"></use></svg><span class="text-primary h5 h-md-4 m-0">'],
        'end_value': ['</span>'],
        'name': 'Markedstid',  # missing, so will need to find it in data!
        'list': False,
        'limit': 1}

    lookout_dict['Link'] = {'start_value': [
        '<a class="btn btn-primary col-12 w-100 font-weight-bolder px-1 ng-star-inserted" data-gtm="see_property_at_agency_btn" target="_blank" href="'],
                            'end_value': ['"'],
                            'name': 'Link',  # missing, so will need to find it in data!
                            'list': False,
                            'limit': 1}

    lookout_dict['Link_alt'] = {
        'start_value': ['btn btn-primary col-12 w-100 font-weight-bolder px-1 ng-star-inserted', 'href="'],
        'end_value': ['"'],
        'name': 'Link_alt',  # missing, so will need to find it in data!
        'list': False,
        'limit': 1}

    # If Failed on basisoplysninger, we can try to add them manually:
#    elements = ['Boligstørrelse', 'Grundstørrelse', 'Byggeår',
#                'Energimærke', 'Ejerudgift', 'Kælderstørrelse',
#                'Boligareal, tinglyst']
#    for element in elements:
#        lookout_dict[element + '_alt'] = {
#            'start_value': [element, '<span _ngcontent-sc', '="" class="d-md-none my-auto">'],
#            'end_value': ['<!---->'],
#            'name': element + '_alt',  # missing, so will need to find it in data!
#            'list': False,
#            'limit': 1}
#
#    for element in elements:
#        lookout_dict[element + '_alt2'] = {
#            'start_value': [element, '<span _ngcontent-sc', '="" class="d-md-none my-auto">'],
#            'end_value': ['</span>'],
#            'name': element + '_alt',  # missing, so will need to find it in data!
#            'list': False,
#            'limit': 1}

    return lookout_dict


def get_start_end(lookout_starts, lookout_ends, content, start=0, end=10e6):
    """
    Description:
        Get start and end of the lookout patterns.
        Used as a helper function to "fetch data"

        Iteratively looks over the "lookout_starts" to determine the final starting position.
        I.e. if lookout_starts has one than one element, it will start by finding the first
        element, then it will continue to find the second element the first time it appears
        after the first one, and so forth with the third element the first time it appears
        after the second. Sample principle holds for the "lookout_ends"
    Input:
        lookout_starts (list): List of element to finde iteratively.
        lookout_ends (list): List of element to find iteratively (startin)
        content (str): Content to be searched
    Returns:
        int: start. Starting position based on lookout_starts
        int: end. Ending position based on lookout_ends
    """

    for lookout_start in lookout_starts:
        start = content.find(lookout_start, start + 1)
    for e, lookout_end in enumerate(lookout_ends):
        if e == 0:
            end = content.find(lookout_end, start + len(lookout_starts[-1]))
        else:
            end = content.rfind(lookout_end, start + len(lookout_starts[-1]), end)

    return start, end


def fetch_data(soup, lookout_dict, threshold_key_len=200):
    """
    Fetches data based on lookout dict from soup

    Input:
        soup (bs4 soup):
        lookout_dict (dict): As defined and described in function "initialize_lookout_dict".
        threshold_key_len (int): To make sure gibberish are not stored!
    Returns:
        dict: Dictionary containing ordered information from the soup based on the lookout patterns in lookout_dict
    """
    bolig_dict = {}
    bolig_dict_temp = {}

    contents = [str(x) for x in soup.find('pre')]
    for content in contents:
        host_identifier = '[_nghost-'
        host_start = content.find(host_identifier)
        host_end = content.find(']', host_start)

        sc_host = 'doesnotmatteranymore'
        for k in lookout_dict:
            # print('Lookout patterns', k,  lookout_dict[k])
            start = 0
            end = len(content)
            counter = 0
            while True:  # I

                if 'name' in lookout_dict[k]:
                    key_in_scope = lookout_dict[k]['name']

                if ('start_key' and 'end_key') in lookout_dict[k]:
                    lookout_starts = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in
                                      lookout_dict[k]['start_key']]  # ['<meta name="keywords" content="">', '<title>']
                    lookout_ends = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k]['end_key']]
                    start, end = get_start_end(lookout_starts, lookout_ends, content, start=start, end=end)
                    key_in_scope = content[start + len(lookout_starts[-1]):end].strip()  # finding key from context

                if ('start_value' and 'end_value') in lookout_dict[k]:
                    lookout_starts = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k][
                        'start_value']]  # ['<meta name="keywords" content="">', '<title>']
                    lookout_ends = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k]['end_value']]
                    start, end = get_start_end(lookout_starts, lookout_ends, content, start=start, end=end)

                counter += 1
                if start != -1:
                    # print('start', start, end)
                    if lookout_dict[k]['list']:
                        if key_in_scope in bolig_dict_temp:
                            bolig_dict_temp[key_in_scope].append(content[start + len(lookout_starts[-1]):end].strip())
                        else:
                            bolig_dict_temp[key_in_scope] = [content[start + len(lookout_starts[-1]):end].strip()]
                    else:
                        id_counter = 2
                        if key_in_scope in bolig_dict_temp:
                            bolig_dict_temp[key_in_scope + str(id_counter)] = content[start + len(
                                lookout_starts[-1]):end].strip()
                        else:
                            bolig_dict_temp[key_in_scope] = content[start + len(lookout_starts[-1]):end].strip()
                        id_counter += 1
                else:
                    break
                if counter >= lookout_dict[k]['limit']:
                    break

        # Cleanup - did we retrieve somethign we didn't want
        for k in bolig_dict_temp:
            if len(k) < threshold_key_len:
                bolig_dict[k] = bolig_dict_temp[k]

        return bolig_dict


def fetch_data_old(soup, lookout_dict, threshold_key_len=200):
    """
    Fetches data based on lookout dict from soup

    Input:
        soup (bs4 soup):
        lookout_dict (dict): As defined and described in function "initialize_lookout_dict".
        threshold_key_len (int): To make sure gibberish are not stored!
    Returns:
        dict: Dictionary containing ordered information from the soup based on the lookout patterns in lookout_dict
    """
    bolig_dict = {}
    bolig_dict_temp = {}

    contents = [str(x) for x in soup.find('pre')]
    for content in contents:
        host_identifier = '[_nghost-'
        host_start = content.find(host_identifier)
        host_end = content.find(']', host_start)
        # sc_host = content[host_start+len(host_identifier):host_end]

        sc_ids = [int(re.search('\d\d*', y).group()) for y in re.findall('sc\d\d*', content)]
        sc_ids = list(set(sc_ids))
        sc_min, sc_max = min(sc_ids), max(sc_ids)
        print('sc min max', sc_min, sc_max)
        print('number of sc', len(sc_ids), sc_ids)
        for sc_host_int in sc_ids:  # range(sc_min,sc_max):
            sc_host = str(sc_host_int)
            # print('this is the host:', sc_host, type)
            for k in lookout_dict:
                # print('Lookout patterns', k,  lookout_dict[k])
                start = 0
                end = len(content)
                counter = 0
                while True:  # I

                    if 'name' in lookout_dict[k]:
                        key_in_scope = lookout_dict[k]['name']

                    if ('start_key' and 'end_key') in lookout_dict[k]:
                        # print('looking for key')
                        # print([(x, re.sub('sc\d\d*', 'sc'+sc_host, x)) for x in lookout_dict[k]['start_key']])
                        lookout_starts = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k][
                            'start_key']]  # ['<meta name="keywords" content="">', '<title>']
                        lookout_ends = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k]['end_key']]
                        start, end = get_start_end(lookout_starts, lookout_ends, content, start=start, end=end)
                        key_in_scope = content[start + len(lookout_starts[-1]):end].strip()  # finding key from context

                    if ('start_value' and 'end_value') in lookout_dict[k]:
                        # print('looking for value')
                        lookout_starts = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k][
                            'start_value']]  # ['<meta name="keywords" content="">', '<title>']
                        lookout_ends = [re.sub('sc\d\d*', 'sc' + sc_host, x) for x in lookout_dict[k]['end_value']]
                        start, end = get_start_end(lookout_starts, lookout_ends, content, start=start, end=end)

                    counter += 1
                    if start != -1:
                        # print('start', start, end)
                        if lookout_dict[k]['list']:
                            if key_in_scope in bolig_dict_temp:
                                bolig_dict_temp[key_in_scope + '_sc_host_' + sc_host].append(
                                    content[start + len(lookout_starts[-1]):end].strip())
                            else:
                                bolig_dict_temp[key_in_scope + '_sc_host_' + sc_host] = [
                                    content[start + len(lookout_starts[-1]):end].strip()]
                        else:
                            id_counter = 2
                            if key_in_scope in bolig_dict_temp:
                                bolig_dict_temp[key_in_scope + str(id_counter) + '_sc_host_' + sc_host] = content[
                                                                                                          start + len(
                                                                                                              lookout_starts[
                                                                                                                  -1]):end].strip()
                            else:
                                bolig_dict_temp[key_in_scope + '_sc_host_' + sc_host] = content[start + len(
                                    lookout_starts[-1]):end].strip()
                            id_counter += 1
                    else:
                        break
                    if counter >= lookout_dict[k]['limit']:
                        break

        # Cleanup - did we retrieve somethign we didn't want
        for k in bolig_dict_temp:
            if len(k) < threshold_key_len:
                bolig_dict[k] = bolig_dict_temp[k]
        return bolig_dict


def cleanup():
    #dir_path = TEMP_DATA_PATH
    files = glob.glob(TEMP_DATA_PATH + r'/*', recursive=True)

    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))

def collect_bolig_data(url):
    """
    Description:
        Collect ordered data from a given url
    Input:
        url (str): URL to fetch data from
    Returns:
        dict: Dictionary containing the fetched information from the url
    """
    time_it = time.time()
    try:
        browser = webdriver.Chrome(ChromeDriverManager().install())
        html = get_html_with_js(url, quit_browser=True, close_tabs=False, browser=browser)
        soup = BeautifulSoup(html, "html.parser")
        lookout_dict = initialize_lookout_dict()
        bolig_data = fetch_data(soup, lookout_dict, threshold_key_len=200)
        bolig_data['boliga_link'] = url
        time_taken = time.time() - time_it

    except Exception as e:
        bolig_data = dict()
        bolig_data['boliga_link'] = url
        bolig_data['error'] = f'Error: {e}'
        time_taken = time.time() - time_it
    return bolig_data, time_taken


if __name__ == '__main__':
    from multiprocessing import Pool

    available_cores = os.cpu_count() - 1
    print('available cores', available_cores)

    for page in range(20, 22):
        print('processing page', page)
        bolig_dict = get_bolig_dict(municipality_code='101', page=page)
        bolig_urls = [f'https://www.boliga.dk{bolig}' for bolig in bolig_dict]

        #result0 = collect_bolig_data(bolig_urls[0])
        #print(result0)


        with Pool(available_cores) as p:
            results = p.map(collect_bolig_data, bolig_urls)

        results_path = f'data/bolig_data/bolig_data_{page}.pickle'
        pickle.dump(results, open(results_path, 'wb'))

        cleanup()
        time.sleep(20)

