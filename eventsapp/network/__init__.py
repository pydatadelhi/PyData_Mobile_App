from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest

import os
import json
import time
import shutil
from functools import partial

app = App.get_running_app()


def is_json(data):
    try:
        json.loads(data)
    except:
        return False
    return True


def write_oldata(fpath, data):
    with open(fpath, 'w') as f:
        f.write(data)


def on_success(oldata, endpoint, req, bl):
    # got new data, update the schedule
    Logger.info('EventsApp: Fetch successful for {}'.format(endpoint))
    ndata = None
    with open(req.file_path) as f:
        ndata = f.read()
    if ndata == oldata:
        Logger.info('EventsApp: New data is same as old data')
        return

    if not is_json(ndata):
        Logger.info('EventsApp: New data is not json, using old data')
        print(ndata)
        write_oldata(req.file_path, oldata)
        return
    # check which endpoint got a response
    scr = {
        'schedule': 'screenschedule',
        'tracks': 'screentalks',
        'sponsors': 'screensponsor',
        'about': 'screenabout',
        'venue': 'screenvenue',
        'community': 'screencommunity',
        'event': 'screenschedule'}[endpoint]
    Logger.info("EventsApp: Got new data for {}".format(endpoint))
    Logger.info("EventsApp: Loading screen {}".format(scr))
    getattr(app, scr).on_enter(onsuccess=True)


def _check_data(req, oldata):
    ndata = None
    with open(req.file_path) as f:
        ndata = f.read()
    if ndata == oldata:
        return
    # data is invalid in file
    # overwrite file with old data
    write_oldata(req.file_path, oldata)


def on_failure(oldata, endpoint, req, bl):
    Logger.info('EventsApp: Failure fetching {}'.format(endpoint))
    Logger.info(bl)
    _check_data(req, oldata)


def on_error(oldata, endpoint, req, bl):
    Logger.info('EventsApp: error fetching {}'.format(endpoint))
    Logger.info(req)
    _check_data(req, oldata)


def fetch_remote_data(dt):
    '''Fetch remote data from the endpoint
    '''
    for args in fetch_remote_data._args:
        endpoint, filepath, oldata = args
        Logger.info("EventsApp: Fetching data {}".format(endpoint))
        UrlRequest(
            #FIXME: initial url should be abstracted out too.
            'https://raw.githubusercontent.com/pydatadelhi/' +\
            'PyData_Mobile_App/master/eventsapp/data/{}.json'.format(endpoint),
            file_path=filepath,
            on_success=partial(on_success, oldata, endpoint),
            on_error=partial(on_error, oldata, endpoint),
            on_failure=partial(on_failure, oldata, endpoint),
            timeout=5)
    fetch_remote_data._args = []

fetch_remote_data._args = []

trigger_fetch_remote_data = Clock.create_trigger(fetch_remote_data, 9)
'''Trigger fetching of data only once every 9 seconds
'''


def get_data(endpoint, onsuccess=False):
    filepath = app.script_path + '/data/' + endpoint + '.json'

    #use old data to check if anything in the data has been updated.
    oldata = None
    with open(filepath) as f:
        oldata = f.read()

    if os.environ.get("PYCONF_OFFLINE_MODE", None) == '1':
        onsuccess = True
    if not onsuccess:
        fetch_remote_data._args.append([endpoint, filepath, oldata])
        trigger_fetch_remote_data()

    try:
        jsondata = json.loads(oldata)
        # Data loaded correctly!
        # Now Same it as old data for use in case of faliures
        shutil.copy(filepath, filepath + '.old')
    except Exception as err:
        print(err)
        # could not load new data, load old working data
        filepath = filepath + '.old'
        with open(filepath) as fd:
            jsondata = json.load(fd)

    return jsondata