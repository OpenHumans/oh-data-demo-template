"""
Asynchronous tasks that update data in Open Humans.
These tasks:
  1. delete any current files in OH if they match the planned upload filename
  2. adds a data file
"""
import logging
import os
import json
import shutil
import tempfile
from django.utils import lorem_ipsum
import textwrap
import requests
from celery import shared_task
from django.conf import settings
from open_humans.models import OpenHumansMember
from datetime import datetime
from demotemplate.settings import rr

# Set up logging.
logger = logging.getLogger(__name__)


@shared_task
def process_source(oh_id):
    """
    Update the data source file for a given OH user
    """
    logger.debug('Starting data source processing for {}'.format(oh_id))
    oh_member = OpenHumansMember.objects.get(oh_id=oh_id)
    oh_access_token = oh_member.get_access_token(
                            client_id=settings.OPENHUMANS_CLIENT_ID,
                            client_secret=settings.OPENHUMANS_CLIENT_SECRET)
    source_data = get_existing_data(oh_access_token)
    datasource_member = oh_member.datasourcemember
    
    update_datasource(oh_member, source_data)

@shared_task
def make_request_respectful_get(url, realms, **kwargs):
    r = rr.get(url=url, realms=realms, **kwargs)
    logger.debug('Request completed. Response: {}'.format(r.text))


def update_datasource(oh_member, source_data):
    try:
        # 1. Set start and end times for API calls- may have to loop over short periods.
        # 2. Get data from API using requests_respectful:
        
        # r = rr.get(url=url, realms=realms, **kwargs)
        # logger.debug('Request completed. Response: {}'.format(r.text))
        # source_data += r.json()

        print('successfully finished update for {}'.format(oh_member.oh_id))
        datasource_member = oh_member.datasourcemember
        datasource_member.last_updated = arrow.now().format()
        datasource_member.save()
    except RequestsRespectfulRateLimitedError:
        logger.debug(
            'requeued processing for {} with 60 secs delay'.format(
                oh_member.oh_id)
                )
        process_source.apply_async(args=[oh_member.oh_id], countdown=61)
    finally:
        replace_datasource(oh_member, source_data)


def replace_datasource(oh_member, source_data):
    # delete old file and upload new to open humans
    tmp_directory = tempfile.mkdtemp()
    metadata = {
        'description':
        'Dummy data for demo.',
        'tags': ['demo', 'dummy', 'test'],
        'updated_at': str(datetime.utcnow()),
        }
    out_file = os.path.join(tmp_directory, 'dummy-data.json')
    logger.debug('deleted old file for {}'.format(oh_member.oh_id))
    api.delete_file(oh_member.access_token,
                    oh_member.oh_id,
                    file_basename="dummy-data.json")
    with open(out_file, 'w') as json_file:
        json.dump(source_data, json_file)
        json_file.flush()
    api.upload_aws(out_file, metadata,
                   oh_member.access_token,
                   project_member_id=oh_member.oh_id)
    logger.debug('uploaded new file for {}'.format(oh_member.oh_id))


def get_start_date(source_data):
    # This function should get a start date for data
    # retrieval, by using the data source API.


def get_existing_data(oh_access_token):
    member = api.exchange_oauth2_member(oh_access_token)
    for dfile in member['data']:
        if 'demo' in dfile['metadata']['tags']:
            # get file here and read the json into memory
            tf_in = tempfile.NamedTemporaryFile(suffix='.json')
            tf_in.write(requests.get(dfile['download_url']).content)
            tf_in.flush()
            demo_data = json.load(open(tf_in.name))
            return demo_data
    return []
