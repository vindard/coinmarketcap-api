import argparse
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

import dateutil.parser


def make_request(url, services_dict, session, service, params=None):
    try:
        url += services_dict[service]
        response = session.get(url, params=params)
        print(response)
        if response.status_code == 401:
            print(f"401 Error: Likely api keys invalid or missing")
            response.raise_for_status()
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

    return json.loads(response.text)

def get_all_ids(url, services_dict, session, mode, force_update):
    filename = f"map-data-{mode}.txt"
    try:
        with open(filename, 'r') as f:
            data = f.read()
            data = json.loads(data)
    except FileNotFoundError:
        data = None
    if not data or force_update:
        data = make_request(url, services_dict, session, service='1')['data']
        with open(filename, 'w') as f:
            f.write(json.dumps(data, indent=2))

    all_ids = []
    for coin in data:
        all_ids.append(coin['id'])

    return all_ids, filename

def chunk_ids(url, services_dict, session, mode, force_update, chunk_size=1000):
    all_ids, _ = get_all_ids(url, services_dict, session, mode, force_update)
    chunks = [
        all_ids[i:i+chunk_size]
        for i in range(0, len(all_ids), chunk_size)
    ]

    return chunks

def fromisoformat(time):
    return dateutil.parser.parse(time).timestamp()

def get_all_quotes(url, services_dict, session, chunked_ids, mode, force_update):
    filename = f"quotes-data-{mode}.txt"
    all_data = {}
    if not force_update:
        try:
            with open(filename, 'r') as f:
                all_data = f.read()
                all_data = json.loads(all_data)
                print("Reading from file...")
        except FileNotFoundError:
            pass

    if not all_data or force_update:
        for chunk in chunked_ids:
            ids = ','.join([str(i) for i in chunk])
            params = {
                'id': ids,
                'convert': 'BTC',
            }
            data = make_request(url, services_dict, session, '5', params)['data']
            all_data = {**all_data, **data}
        for i in all_data:
            all_data[i].pop("tags", None)
            all_data[i].pop("platform", None)
            all_data[i]['date_added'] = fromisoformat(all_data[i]['date_added'])
            all_data[i]['last_updated'] = fromisoformat(all_data[i]['last_updated'])
            all_data[i]['quote']['BTC']['last_updated'] = fromisoformat(all_data[i]['quote']['BTC']['last_updated'])

    with open(filename, 'w') as f:
        f.write(json.dumps(all_data, indent=2))

    return all_data, filename

def run(mode='sandbox', force_update=False):
    update_state_string = "enabled" if force_update else "disabled"
    print(f"Running in \"{mode}\" mode with forced data update \"{update_state_string}\".")

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
    url = creds[mode]["url"]
    api_key = creds[mode]["api_key"]

    services_dict = {
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

    chunked_ids = chunk_ids(url, services_dict, session, mode, force_update)
    all_data, quotes_file = get_all_quotes(url, services_dict, session, chunked_ids, mode, force_update)
    print(f"Finished, quotes data stored at: {quotes_file}")

    return all_data


if __name__ == "__main__":
    # Argument Parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="Force an api check regardless of data state.")
    parser.add_argument("--pro", action="store_true", help="Force an api check regardless of data state.")
    args = parser.parse_args()

    # Choose between "sandbox" or "pro"
    MODE = "sandbox" if not args.pro else "pro"
    UPDATE = args.update

    run(mode=MODE, force_update=UPDATE)