import requests


def call(self, endpoint, data=None, method='GET'):
    if data is None:
        data = {}

    if self._auth_token:
        data.update({'auth_token': self._auth_token})
    elif self._access_token:
        data.update({'access_token': self._access_token})

    url = f'{self._base_url}{endpoint}'
    result = None

    if method == 'GET':
        result = requests.get(url, data)

    if method == 'POST':
        result = requests.post(url, data)

    if method == 'PUT':
        result = requests.put(url, data)

    if not result.status_code == requests.codes.ok:
        raise Exception(f'API request failed with code {result.status_code}: {result.text}')

    # self._persist_result(endpoint, result)

    return None if result is None else result.json()

