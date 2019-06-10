from buildstream.testing import cli     # noqa: F401
import pytest


#
# This file is loaded by pytest, we use it to add a custom
# `--integration` option to our test suite, and to install
# a session scope fixture.
#


#################################################
#            Implement pytest option            #
#################################################
def pytest_addoption(parser):
    parser.addoption('--docker', action='store_true', default=False,
                     help='Run tests that require docker daemon running')


def pytest_configure(config):
    config.addinivalue_line("markers", "docker: mark test as requiring docker daemon")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--docker"):
        # do not skip docker tests
        return
    docker_tests = pytest.mark.skip(reason="need --docker flag to run")
    for item in items:
        if "docker" in item.keywords:
            item.add_marker(docker_tests)
