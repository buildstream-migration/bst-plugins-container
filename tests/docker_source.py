import os
import pytest

from buildstream.plugintestutils import cli

from tests.testutils import plugin_import


DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'docker-source'
)


@pytest.mark.datafiles(DATA_DIR)
def test_docker_fetch(cli, datafiles, plugin_import):
    project = os.path.join(datafiles.dirname, datafiles.basename)
    result = cli.run(project=project, args=['source', 'fetch', 'dockerhub-alpine.bst'])
    result.assert_success()


@pytest.mark.datafiles(DATA_DIR)
def test_docker_source_checkout(cli, datafiles, plugin_import):
    project = os.path.join(datafiles.dirname, datafiles.basename)
    checkout = os.path.join(cli.directory, 'checkout')
    result = cli.run(project=project, args=['source', 'checkout', '--fetch', 'dockerhub-alpine.bst', checkout])
    result.assert_success()
    # Rather than make assertions about the whole Alpine Linux image, verify
    # that the /etc/os-release file exists as a sanity check.
    assert os.path.isfile(os.path.join(checkout, 'dockerhub-alpine/etc/os-release'))
