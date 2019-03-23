#! /bin/sh
coverage erase
pytest --ds tests.test_project.project.settings.test
pytest --cov-report=html --ds tests.test_project.project.settings.relay
