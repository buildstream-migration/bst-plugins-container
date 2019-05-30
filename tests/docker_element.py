import os
import pytest

from buildstream.testing.runcli import cli_integration as cli
from buildstream.testing.integration import integration_cache
from buildstream.testing._utils.site import HAVE_SANDBOX

DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'project'
)


@pytest.mark.datafiles(DATA_DIR)
@pytest.mark.skipif(not HAVE_SANDBOX, reason='Only available with a functioning sandbox')
def test_single_build_dep_docker_image(cli, datafiles):
    project = os.path.join(datafiles.dirname, datafiles.basename)
    result = cli.run(project=project, args=['build', 'hello.bst'])
    result.assert_success()
