# wagtail-graphql
> An app to automatically add graphql support to a Wagtail website 

This [Wagtail](https://wagtail.io/) adds [GraphQL](https://graphql.org/) types to 
other Wagtail apps. The objective is for this library to interact with an existing website
in a generic way and with minimal effort.
In particular, it makes minimal assumptions about the structure of the website
to allow for a generic API.       


## Installing / Getting started

To install as a general app:

```shell
pip install wagtail-graphql
```

Add it together with [graphene_django](https://github.com/graphql-python/graphene-django) to the Django INSTALLED_APPS:

```
INSTALLED_APPS = [
    ...
    
    'wagtail_graphql',
    'graphene_django',
    
    ...
]

```


### Initial Configuration

Add the [graphene](https://github.com/graphql-python/graphene) schema `GRAPHENE` and a `GRAPHQL_API` dictionary.   
Include all the Wagtail apps the library should generate bindings to `APPS` and optionally
specify the prefix for each app in `PREFIX`. To remove a leading part of all the urls, specify the `URL_PREFIX` parameter.

```python
GRAPHENE = {
    'SCHEMA': 'wagtail_graphql.schema.schema',
}

GRAPHQL_API = {
    'APPS': [
        'home'
    ],
    'PREFIX': {
        'home': ''
    },
    'URL_PREFIX': '/home'
}
```
The example above generates bindings for the `home` app.  Every url in this example
will be stripped of the initial `/home` substring.  


## Developing

To develop this library, download the source code and install a local version in your Wagtail website.


## Features

This project is intended to require minimal configuration and interaction: 
* Supports [Page models](https://docs.wagtail.io/en/master/topics/pages.html)
* [Snippets](https://docs.wagtail.io/en/master/topics/snippets.html)
* Images
* Documents
* StreamFields, StreamBlocks, and StructBlocks
 

## Contributing

If you'd like to contribute, please fork the repository and use a feature
branch. Pull requests are welcome.

## Links

- Repository: https://github.com/tr11/wagtail-graphql
- Issue tracker: https://github.com/tr11/wagtail-graphql/issues

## Licensing

The code in this project is licensed under MIT license.