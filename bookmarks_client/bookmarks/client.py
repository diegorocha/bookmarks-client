from django.conf import settings
from requests import get, post, put, delete


class BookmarkClient(object):
    def __init__(self, token=''):
        self.base_url = settings.URL_API
        self.token = token

    def _get_headers(self):
        return {'Authorization': 'JWT %s' % self.token}

    def _get_url(self, endpoint, _id=''):
        endpoint = '%s/%s' % (self.base_url, endpoint)
        if id:
            endpoint += '/' + str(_id)
        return endpoint

    def sign_in(self, name, email, password):
        endpoint = self._get_url('users')
        data = {'name': name, 'email': email, 'password': password, 'isAdmin': False}
        r = post(endpoint, json=data)
        if r.ok:
            self.login(email, password)
        return r.ok

    def new_admin(self, name, email, password):
        endpoint = self._get_url('users')
        data = {'name': name, 'email': email, 'password': password, 'isAdmin': True}
        r = post(endpoint, json=data)
        return r.ok

    def login(self, user, password):
        endpoint = self._get_url('auth')
        data = {'email': user, 'password': password}
        r = post(endpoint, json=data)
        if r.ok:
            self.token = r.json()['token']
            return True
        return False

    def get_bookmarks(self):
        endpoint = self._get_url('bookmarks')
        r = get(endpoint, headers=self._get_headers())
        try:
            return r.json()
        except:
            return []

    def get_user(self):
        endpoint = self._get_url('user')
        r = get(endpoint, headers=self._get_headers())
        try:
            return r.json()
        except:
            return {}

    def new_bookmark(self, title, url):
        endpoint = self._get_url('bookmarks')
        data = {'title': title, 'url': url}
        r = post(endpoint, headers=self._get_headers(), json=data)
        return r.ok

    def update_bookmark(self, _id, title, url):
        endpoint = self._get_url('bookmarks', _id)
        data = {'title': title, 'url': url}
        r = put(endpoint, headers=self._get_headers(), json=data)
        return r.ok

    def delete_bookmark(self, _id):
        endpoint = self._get_url('bookmarks', _id)
        r = delete(endpoint, headers=self._get_headers())
        return r.ok

    def get_all_users(self):
        endpoint = self._get_url('users/all')
        r = get(endpoint, headers=self._get_headers())
        try:
            return r.json()
        except:
            return []

    def get_all_bookmarks(self):
        endpoint = self._get_url('bookmarks/all')
        r = get(endpoint, headers=self._get_headers())
        try:
            return r.json()
        except:
            return []