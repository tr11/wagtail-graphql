import json
import os.path


def get_query(*name):
    name = '_'.join(name)
    folder = os.path.dirname(__file__)
    query = open(os.path.join(folder, name + '.graphql'), 'rt').read()
    result = json.load(open(os.path.join(folder, name + '.json'), 'rt'))
    return query, result


def assert_query(client, *name):
    query, result = get_query(*name)
    response = client.post('/graphql', {"query": query})
    assert response.status_code == 200
    response_json = response.json()
    assert 'errors' not in response_json

    print(result)
    print(response_json)

    assert result == response_json
