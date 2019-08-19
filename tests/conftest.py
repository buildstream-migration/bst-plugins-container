import socket
import time

from buildstream.testing import cli     # noqa: F401
import docker
import pytest

from tests.utils import get_docker_host

DOCKER_REGISTRY_IMAGE = "registry:2"
DOCKER_REGISTRY_PORT = 5000

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
    start_images = set(docker_client.images.list())
    yield
    end_images = set(docker_client.images.list())
    # delete generated images from host Docker registry
    images_to_delete = end_images.difference(start_images)
    for image_id in map(lambda image: image.id.split(':')[1], images_to_delete):
        docker_client.images.remove(image_id, force=True)
    assert start_images == set(docker_client.images.list())


@pytest.fixture(scope="session")
def docker_registry(docker_client, teardown_generated_test_images):
    """
    This fixture returns the address and port for the engine to reach the registry.
    Depends on teardown_generated_test_images fixture to ensure that images are
    only cleaned up after this fixture completes.
    """
    docker_client.images.pull(DOCKER_REGISTRY_IMAGE)
    engine_to_registry = "localhost"  # the hostname the Docker engine addresses the Docker registry service
    engine_url = get_docker_host(docker_client)

    container = docker_client.containers.run(
        DOCKER_REGISTRY_IMAGE,
        ports={DOCKER_REGISTRY_PORT: DOCKER_REGISTRY_PORT},
        detach=True,
        auto_remove=True,
        name='registry'
    )

    try:
        # check that registry can be reached from namespace running test
        _wait_for_socket(engine_url, DOCKER_REGISTRY_PORT, 20)
        yield "{}:{}".format(engine_to_registry, DOCKER_REGISTRY_PORT)
    finally:
        container.stop(timeout=1)


def _wait_for_socket(host, port, seconds):
    for _ in range(10 * seconds):
        try:
            socket.create_connection((host, port)).close()
        except ConnectionRefusedError:
            time.sleep(0.1)
        else:
            break
    else:
        raise Exception("timed out waiting for port {}:{} to open".format(host, port))
