#!/usr/bin/python

import time
import requests
from getpass import getpass
from ConfigParser import SafeConfigParser

CONFIG_FILE = '/etc/lisa_scraper.cfg'

def main():
    
    config = SafeConfigParser()

    config.read(CONFIG_FILE)

    username = config.get('confluence', 'username')
    password = config.get('confluence', 'password')

    officilitation_users = config.get('confluence', 'officilitation_users').split(',')

    api_url = config.get('confluence', 'api_url')
    page_id = config.getint('confluence', 'page_id')

    # Used for the API calls to get history
    full_url = '{}/content/{}/history'.format(api_url, page_id)
    
    # Compact URL to send to users to follow upon alert
    message_url = config.get('confluence', 'message_url')

    check_period_s = config.getint('confluence', 'check_period_s')

    # Prowl config
    prowl_api_keys = config.get('prowl', 'api_keys').split(',')

    alert_sent = False

    error_count = 0
    error_notify_threshold = 5

    while True:

        req = requests.get(full_url, params={ 'expand': 'lastUpdated' }, auth=(username, password))

        try:

            req.raise_for_status()
            data = req.json()

        except (ValueError, requests.exceptions.HTTPError) as err:

            error_count += 1

            if error_count > error_notify_threshold:

                send_prowl_alert('AWOOGA: {}'.format(err), prowl_api_keys)
                raise

        else:

            if error_count > 0:

                error_count = 0


        if (
             'lastUpdated' in data and
             data['lastUpdated']['by']['username'] in officilitation_users
           ):

            if not alert_sent:
                send_prowl_alert('Go sign up!\n{}'.format(message_url), prowl_api_keys)

            alert_sent = True

            print 'Change detected'
        else:

            alert_sent = False
            print 'No change'

        time.sleep(check_period_s)


def send_prowl_alert(message, prowl_api_keys):

    prowl_url = 'https://prowlapp.com/publicapi/add'

    for prowl_user_key in prowl_api_keys:

        payload = {
                    'apikey': prowl_user_key,
                    'application': 'JamfMassage:',
                    'description': message,
                    'priority': 2,
                   }

        req = requests.get(prowl_url, params=payload)
        req.raise_for_status()

main()
