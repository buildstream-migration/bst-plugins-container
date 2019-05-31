import os
import pytest
import stat
import docker
from buildstream.testing.runcli import cli_integration as cli
from buildstream.testing.integration import integration_cache
from buildstream.testing._utils.site import HAVE_SANDBOX

pytestmark = pytest.mark.integration

DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'project'
)


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.skipif(not HAVE_SANDBOX, reason='Only available with a functioning sandbox')
def test_single_build_dep_docker_image(cli, datafiles, tmp_path):

    # build image
    project = os.path.join(datafiles.dirname, datafiles.basename)
    hello_exec = os.path.join(project, 'files', 'hello-world-image-fs', 'hello')
    # need to set permission as copying files into `DATA_DIR` changes permissions
    os.chmod(hello_exec, 0o755)
    test_element = 'hello-world-image.bst'
    result = cli.run(project=project, args=['build', test_element])
    result.assert_success()
    checkout_dir = os.path.join(tmp_path, 'checkout')
    os.makedirs(checkout_dir)
    result = cli.run(project=project, args=['artifact', 'checkout', '--directory', checkout_dir, test_element])
    result.assert_success()

    # load docker image
    client = docker.from_env()
    artifact_name = 'image.tar'
    image_path = str(os.path.join(checkout_dir, artifact_name))
    with open(image_path, 'rb') as image_handle:
        # response is a list of images
        response = client.images.load(image_handle.read())
        # get first tag of first image
        tag = response[0].tags[0]

    # compare output of docker run
    output = client.containers.run(tag).decode('utf-8')
    with open(os.path.join(project, 'files', 'hello-world_output.txt'), 'r') as expected_output:
        assert output == expected_output.read()


def _parse_docker_load_output(result):
    result_list = result.split(':')
    return result_list[-2][1:]
