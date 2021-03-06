"""Code to scrape text off of WTA website"""
# Code from: https://github.com/Jadetabony/wta_hikes
# Ensure you create a 'washington_hikes.csv' file with the following line:
# hike_name,region,length,elevation gain,rating,number_votes,features,which_pass,lat,long,numReports

from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

# Regular expressions match the text before and after latitude and
# longitude coordinates embedded in a URL in the trail description web page.
PREFIX_REGEX = re.compile("//www.google.com/maps/dir//")
SUFFIX_REGEX = re.compile("/@\S+en")

NUMBER_OF_TRAILS_PER_PAGE = 30
TOTAL_NUMBER_OF_PAGES = 113

def collect_hikeurls(starturl):
    """Collecting all of the websites for all of the hikes"""
    hike_links = []
    path = starturl
    counter = 0
    while True:
        r = requests.get(path)
        soup = BeautifulSoup(r.text, 'lxml')
        for div in soup.findAll('a', attrs={'class': 'listitem-title'}):
            hike_links.append(div['href'])
            counter += 1
        print 'Collected %d websites' % counter
        link = soup.find('span', attrs={'class': 'next'})
        if link is None:
            break
        else:
            path = link.a['href']
    return hike_links

def extract_lat_long(location_url):
    # Uses regular expressions to extract lat and long from URL
    # by stripping off leading and following text, leaving a
    # comma-separated latitude, longitude coordinates.
    start_lat_index = PREFIX_REGEX.match(location_url).end()
    end_long_index = len(location_url) - len(SUFFIX_REGEX.findall(location_url)[0])
    lat_long = location_url[start_lat_index : end_long_index]
    return lat_long.split(",")

def parser(url):
    """Parses URL into hiking dataset.

    Parser collects html soup and populates
    washington_hikes table with relevant data. Data cleaning is completed in a
    seperate python script."""

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    row_data = {}
    row_data['hike_name'] = soup.find('h1', attrs={'class': "documentFirstHeading"}).text.strip()
    try:
        row_data['region'] = soup.find('div', attrs={'class': "hike-stat grid_3 alpha"}).div.text.strip()
    except:
        try:
            row_data['region'] = soup.find('div', attrs={'id': 'hike-region'}).span.text
        except:
            row_data['region'] = 'NR'
    try:
        lengain = []
        for div in soup.findAll('div', attrs={'class': "hike-stat grid_3"}):
            lengain.append(div.div.span.text)
        row_data['length'] = lengain[0]
        row_data['elevation gain'] = lengain[1]
    except:
        row_data['length'] = 'NR'
        row_data['elevation gain'] = 'NR'
    try:
        row_data['rating'] = soup.find('div', attrs={'class': "current-rating"}).text
    except:
        row_data['rating'] = 'NR'
    try:
        row_data['number_votes'] = soup.find('div', attrs={'class': "rating-count"}).text
    except:
        row_data['number_votes'] = 'NR'
    try:
        features = []
        for div in soup.findAll('div', attrs={'class': "feature grid_1 "}):
            features.append(div['data-title'])
        row_data['features'] = features
    except:
        row_data['features'] = 'NR'
    try:
        row_data['which_pass'] = soup.find('div', attrs={'id': "pass-required-info"}).a.text
    except:
        row_data['which_pass'] = 'NR'
    try:
        lat_long = extract_lat_long(soup.find('a', attrs={'class': "visualNoPrint full-map"})['href'])
        row_data['lat'] = lat_long[0]
        row_data['long'] = lat_long[1]
    except:
        row_data['lat'] = 'NR'
        row_data['long'] = 'NR'
    try:
        row_data['numReports'] = soup.find('span', attrs={'class': 'ReportCount'}).text
    except:
        row_data['numReports'] = 'NR'
    row_data['url'] = url
    return row_data


def build_dataset(data, urls, row = -1):
    """Adds parsed fields to dataset.

    Runs though links in urls and applies parser function to the soup Collected
    from the link.

    data: dataset to append data to

    urls: List of urls"""
    for lnk in urls:
        row += 1
        d = parser(lnk)
        for key in d.keys():
            data.set_value(row, key, d[key])


def getting_hike_desc(url):
    """Collects hike description from url."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        return soup.find('div', attrs={'id': 'hike-body-text'}).p.text
    except:
        return None


if __name__ == '__main__':
    data = pd.read_csv('washington_hikes.csv')
    for page in range(TOTAL_NUMBER_OF_PAGES):
        index = page * NUMBER_OF_TRAILS_PER_PAGE
        print 'Scraping hikes on page #%d' % (page + 1)
        urls = collect_hikeurls('http://www.wta.org/go-outside/hikes?b_start:int=%d' % index)
        build_dataset(data, urls, index - 1)
    data.to_csv('washington_hikes.csv', header=True, encoding='utf-8')
