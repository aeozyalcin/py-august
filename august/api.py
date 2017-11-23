# https://github.com/mlamoure/Indigo-August-Home/blob/master/August%20Home.indigoPlugin/Contents/Server%20Plugin/plugin.py
import logging

import requests

from august.doorbell import Doorbell
from august.activity import DoorbellDingActivity, DoorbellMotionActivity

HEADER_ACCEPT_VERSION = "Accept-Version"
HEADER_AUGUST_ACCESS_TOKEN = "x-august-access-token"
HEADER_AUGUST_API_KEY = "x-august-api-key"
HEADER_KEASE_API_KEY = "x-kease-api-key"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_USER_AGENT = "User-Agent"

HEADER_VALUE_API_KEY = "727dba56-fe45-498d-b4aa-293f96aae0e5"
HEADER_VALUE_CONTENT_TYPE = "application/json"
HEADER_VALUE_USER_AGENT = "August/Luna-3.2.2"
HEADER_VALUE_ACCEPT_VERSION = "0.0.1"

API_GET_SESSION_URL = "https://api-production.august.com/session"
API_SEND_VERIFICATION_CODE_URLS = {
    "phone": "https://api-production.august.com/validation/phone",
    "email": "https://api-production.august.com/validation/email",
}
API_VALIDATE_VERIFICATION_CODE_URLS = {
    "phone": "https://api-production.august.com/validate/phone",
    "email": "https://api-production.august.com/validate/email",
}
API_GET_DOORBELLS_URL = "https://api-production.august.com/users/doorbells/mine"
API_GET_LOCKS_URL = "https://api-production.august.com/users/locks/mine"
API_GET_HOUSE_ACTIVITIES_URL = "https://api-production.august.com/houses/{house_id}/activities"
API_GET_LOCK_URL = "https://api-production.august.com/locks/{lock_id}"
API_GET_LOCK_STATUS_URL = "https://api-production.august.com/locks/{lock_id}/status"
API_WAKEUP_DOORBELL_URL = "https://api-production.august.com/doorbells/{doorbell_id}/wakeup"

_LOGGER = logging.getLogger(__name__)


class Api:
    def __init__(self, timeout=10):
        self._timeout = timeout

    def get_session(self, install_id, identifier, password):
        response = self._call_api(
            "post",
            API_GET_SESSION_URL,
            json={
                "installId": install_id,
                "identifier": identifier,
                "password": password,
            })

        return response

    def send_verification_code(self, access_token, login_method, username):
        response = self._call_api(
            "post",
            API_SEND_VERIFICATION_CODE_URLS[login_method],
            access_token=access_token,
            json={
                "value": username
            })

        return response

    def validate_verification_code(self, access_token, login_method, username,
                                   verification_code):
        response = self._call_api(
            "post",
            API_VALIDATE_VERIFICATION_CODE_URLS[login_method],
            access_token=access_token,
            json={
                login_method: username,
                "code": str(verification_code)
            })

        return response

    def get_doorbells(self, access_token):
        json = self._call_api(
            "get",
            API_GET_DOORBELLS_URL,
            access_token=access_token).json()

        return [Doorbell(data) for data in json.values()]

    def get_locks(self, access_token):
        response = self._call_api(
            "get",
            API_GET_LOCKS_URL,
            access_token=access_token)

        return response.json()

    def get_house_activities(self, access_token, house_id, limit=8):
        response = self._call_api(
            "get",
            API_GET_HOUSE_ACTIVITIES_URL.format(house_id=house_id),
            access_token=access_token,
            params={
                "limit": limit,
            })
        
        activities = []
        for activity_json in response.json():
            if activity_json.get("action") == "doorbell_motion_detected":
                activities.append(DoorbellMotionActivity(activity_json))
            elif activity_json.get("action") == "doorbell_call_missed":
                activities.append(DoorbellDingActivity(activity_json))
        
        return activities

    def get_lock(self, lock_id, access_token):
        response = self._call_api(
            "get",
            API_GET_LOCK_URL.format(lock_id=lock_id),
            access_token=access_token)

        return response.json()

    def get_lock_status(self, lock_id, access_token):
        response = self._call_api(
            "get",
            API_GET_LOCK_STATUS_URL.format(lock_id=lock_id),
            access_token=access_token)

        return response.json()

    def wakeup_doorbell(self, access_token, doorbell_id):
        self._call_api(
            "put",
            API_WAKEUP_DOORBELL_URL.format(doorbell_id=doorbell_id),
            access_token=access_token)

        return True

    def _call_api(self, method, url, access_token=None, params=None, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = self._api_headers(access_token=access_token)

        _LOGGER.debug("About to call %s with header=%s and params=%s", url,
                      kwargs["headers"], params)

        response = requests.request(method, url, params=params,
                                    timeout=self._timeout, **kwargs)

        _LOGGER.debug("Received API response: %s, %s", response.status_code,
                      response.content)

        response.raise_for_status()
        return response

    def _api_headers(self, access_token=None):
        headers = {
            HEADER_ACCEPT_VERSION: HEADER_VALUE_ACCEPT_VERSION,
            HEADER_AUGUST_API_KEY: HEADER_VALUE_API_KEY,
            HEADER_KEASE_API_KEY: HEADER_VALUE_API_KEY,
            HEADER_CONTENT_TYPE: HEADER_VALUE_CONTENT_TYPE,
            HEADER_USER_AGENT: HEADER_VALUE_USER_AGENT,
        }

        if access_token:
            headers[HEADER_AUGUST_ACCESS_TOKEN] = access_token

        return headers
