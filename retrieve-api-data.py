import argparse
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


def make_request(url, service, params=None):
    try:
        url += services[service]
        response = session.get(url, params=params)
        print(response)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    
    return json.loads(response.text)

def get_all_ids(url):
    filename = f"map-data-{MODE}.txt"
    try:
        with open(filename, 'r') as f:
            data = f.read()
            data = json.loads(data)
    except FileNotFoundError:
        data = None
    if not data or UPDATE:
        data = make_request(url, '1')['data']
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=2))

    all_ids = []
    for coin in data:
        all_ids.append(coin['id'])

    return all_ids, filename

def chunk_ids(url, chunk_size=1000):
    all_ids, _ = get_all_ids(url)
    chunks = [
        all_ids[i:i+chunk_size]
        for i in range(0, len(all_ids), chunk_size)
    ]

    return chunks

def get_all_quotes(url, chunked_ids):
    filename = f"quotes-data-{MODE}.txt"

    try:
        with open(filename, 'r') as f:
            all_data = f.read()
            all_data = json.loads(all_data)
    except FileNotFoundError:
        all_data = {}

    if not all_data or UPDATE:
        for chunk in chunked_ids:
            ids = ','.join([str(i) for i in chunk])
            params = {
                'id': ids,
                'convert': 'BTC',
            }
            data = make_request(url, '5', params)['data']
            all_data = {**all_data, **data}
        
    with open(filename, 'w') as f:
        f.write(json.dumps(all_data, indent=2))
    
    return all_data, filename
    


if __name__ == "__main__":
    # Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="Force an api check regardless of data state.")
    parser.add_argument("--pro", action="store_true", help="Force an api check regardless of data state.")
    args = parser.parse_args()

    # Choose between "sandbox" or "pro"
    MODE = "sandbox" if not args.pro else "pro"
    UPDATE = args.update
    
    update_state_string = "enabled" if UPDATE else "disabled"
    print(f"Running in \"{MODE}\" mode with forced data update \"{update_state_string}\".\n")

    creds = {
        "sandbox": {
            "url": 'https://sandbox-api.coinmarketcap.com',
            "api_key": ""
        },
        "pro": {
            "url": "https://pro-api.coinmarketcap.com", 
            "api_key": ""
        }
    }
    url = creds[MODE]["url"]
    api_key = creds[MODE]["api_key"]

    services = {
        '1':'/v1/cryptocurrency/map',
        '2':'/v1/cryptocurrency/info',
        '3':'/v1/cryptocurrency/listings/latest',
        '4':'/v1/cryptocurrency/listings/historical',
        '5':'/v1/cryptocurrency/quotes/latest',
        '6':'/v1/cryptocurrency/quotes/historical',
        '7':'/v1/cryptocurrency/market-pairs/latest',
        '8':'/v1/cryptocurrency/ohlcv/latest',
        '9':'/v1/cryptocurrency/ohlcv/historical',
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    session = Session()
    session.headers.update(headers)

    chunked_ids = chunk_ids(url)
    all_data, quotes_file = get_all_quotes(url, chunked_ids)
    print(f"Finished, quotes data stored at: {quotes_file}")


