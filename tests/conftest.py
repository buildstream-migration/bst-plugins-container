from buildstream.testing import cli     # noqa: F401

import pytest
import docker


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

#################################################
#               Implement fixtures              #
#################################################
@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env()


@pytest.fixture(autouse=True, scope="session")
def teardown_generated_test_images(docker_client):
    yield
    images = docker_client.images.list('bst-plugins-container-tests/*')
    # delete generated images from host Docker registry
    for image_id in map(lambda image: image.id.split(':')[1], images):
        docker_client.images.remove(image_id, force=True)
