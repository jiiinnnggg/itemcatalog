from __future__ import print_function
from collections import namedtuple
import json
import requests
import pprint

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# yelp API info
API_KEY = json.loads(
    open('/var/www/itemcatalog/itemcatalog/yelp_client_secrets.json', 'r').read())['web']['client_secret']

# Yelp API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# generic request function for yelp, pass in generic params
def yelp_request(host, path, api_key, url_params=None):
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
        }
    print(u'Querying {0} ...'.format(url))
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


# search function for yelp based on term and location
def term_loc_search(api_key, term, location, search_limit):
    url_params = {
        'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'limit': search_limit
    }
    return yelp_request(API_HOST, SEARCH_PATH,
                        api_key, url_params=url_params)


# search by yelp business id
def get_business(api_key, business_id):
    business_path = BUSINESS_PATH + business_id
    return yelp_request(API_HOST, business_path, api_key)


# put it all together
def query_api(term, location, search_limit=None):
    search_limit = search_limit or 3
    response = term_loc_search(API_KEY, term, location, search_limit)
    businesses = response.get('businesses')

    if not businesses:
        print(u'No businesses for {0} in {1} found.'.format(term, location))
        return

    print(u"""{0} businesses found, querying business info
          for the top results...""".format(len(businesses)))

    businesses_info = {}
    for x in range(0, len(businesses)):
        biz_address = businesses[x]['location']['display_address']
        biz_address_str = ", ".join(biz_address)
        if 'price' in businesses[x]:
            pr = businesses[x]['price']
        else:
            pr = ""

        businesses_info[x] = {
            "id_name": businesses[x]['id'],
            "name": businesses[x]['name'],
            "url": "https://www.yelp.com/biz/"+businesses[x]['id'],
            "phone": businesses[x]['display_phone'],
            "rating": businesses[x]['rating'],
            "review_count": businesses[x]['review_count'],
            "price": pr,
            "image_url": businesses[x]['image_url'],
            "image_url_sm":
                businesses[x]['image_url'].replace("o.jpg", "120s.jpg"),
            "image_url_med":
                businesses[x]['image_url'].replace("o.jpg", "300s.jpg"),
            "address": biz_address_str
            }

    pprint.pprint(businesses_info)
    return businesses_info


def render_ntuples(businesses_info):
    api_result = businesses_info
    businesses = {}
    for i in range(0, len(api_result)):
        biz = api_result.items()[i][1]
        bkey = biz['id_name']
        businesses[bkey] = namedtuple("Business", biz.keys())(*biz.values())
    ntuples = businesses.values()
    return ntuples
