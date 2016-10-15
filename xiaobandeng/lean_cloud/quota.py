from __future__ import absolute_import

import logging

import leancloud


def get_client_quota(app_id):
    client_quota = leancloud.Object.extend('ClientQuota')
    result = client_quota.query.equal_to("app_id", app_id).find()

    if len(result) == 1:
        return result[0]

    raise Exception("not found client quota for the app_is")


def get_quota(app_id):
    try:
        quota = get_client_quota(app_id)
        access_count = quota.get('access_count', 0)
        access_quota = quota.get('access_quota', 0)
        return (access_count, access_quota)
    except Exception as e:
        logging.error(e)
        return (0, 0)


def update_access_count(app_id, count=1):
    try:
        quota = get_client_quota(app_id)
        quota.increment('access_count', count)
        quota.fetch_when_save = True
        quota.save()
    except Exception as e:
        logging.error(e)
