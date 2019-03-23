import pytest
import json


@pytest.mark.django_db
def test_form_1(client):
    query = """
    mutation($values: GenericScalar) {
        testApp1FormPage(url: "/form", values: $values) {
        result
        errors {
          name
          errors
        }
      }
    }
    """
    variables = json.dumps({
      "values": {"label-1": "1", "other-label": 2}
    })

    response = client.post('/graphql', {"query": query, "variables": variables})
    print(response)
    print(response.json())
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['data']['testApp1FormPage']['errors'] is None
    assert response_json['data']['testApp1FormPage']['result'] == 'OK'


@pytest.mark.django_db
def test_form_fail_1(client):
    query = """
    mutation($values: GenericScalar) {
        testApp1FormPage(url: "/form", values: $values) {
        result
        errors {
          name
          errors
        }
      }
    }
    """
    variables = json.dumps({
      "values": {"label-fail": "1", "other-label": 2}
    })

    response = client.post('/graphql', {"query": query, "variables": variables})
    print(response)
    print(response.json())
    assert response.status_code == 200
    response_json = response.json()
    assert response_json['data']['testApp1FormPage']['errors'] is not None
    assert {'name': 'label-1', 'errors': ['This field is required.']}\
        in response_json['data']['testApp1FormPage']['errors']
    assert response_json['data']['testApp1FormPage']['result'] == 'FAIL'


@pytest.mark.django_db
def test_form_fields(client):
    query = """
        query {
          page(id: 6) {
            ... on Test_app_1FormPage {
              formFields {
                name
                fieldType
                helpText
                required
                choices
                defaultValue
                label
              }
            }
          }
        }
    """
    response = client.post('/graphql', {"query": query})
    print(response)
    print(response.json())

    assert response.json() == {
      "data": {
        "page": {
          "formFields": [
            {
              "choices": "",
              "defaultValue": "default",
              "fieldType": "singleline",
              "helpText": "Help",
              "label": "Label 1",
              "name": "label-1",
              "required": True
            },
            {
              "choices": "",
              "defaultValue": "1",
              "fieldType": "number",
              "helpText": "",
              "label": "other label",
              "name": "other-label",
              "required": False
            }
          ]
        }
      }
    }
