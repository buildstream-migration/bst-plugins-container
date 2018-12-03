import os
import pytest

from tests.testutils import cli_integration, cli, plugin_import
from tests.testutils.integration import assert_contains


DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "docker_source"
)

@pytest.mark.datafiles(DATA_DIR)
def test_docker_fetch(cli, datafiles, plugin_import):

    project = os.path.join(datafiles.dirname, datafiles.basename)
    docker_alpine_base = 'dockerhub-alpine.bst'

    result = cli.run(project=project, args=['fetch', docker_alpine_base])
    result.assert_success()

@pytest.mark.integration
@pytest.mark.datafiles(DATA_DIR)
def test_docker_source_build(cli_integration, datafiles, plugin_import):

    project = os.path.join(datafiles.dirname, datafiles.basename)
    checkout = os.path.join(cli_integration.directory, 'checkout')
    element_name = 'docker-source-test.bst'

    result = cli_integration.run(project=project, args=['build', element_name])
    result.assert_success()

    result = cli_integration.run(project=project, args=['checkout', element_name, checkout])
    result.assert_success()

    assert_contains(checkout, ['/etc/os-release'])
