import hashlib
import os
import tarfile

IMAGE_PREFIX = 'bst-plugins-container-tests'


def push_image(docker_client, registry_url, image_name):
    """Push image_name to registry

    :param docker_client: handle to Docker engine
    :param registry_url: registry to push image to
    :param image_name: name of image to be pushed
    """
    remote_tag = '{}/{}'.format(registry_url, image_name)
    image = docker_client.images.get(image_name)
    image.tag(remote_tag)
    response = list(docker_client.images.push(remote_tag, stream=True, decode=True))
    # check that image was pushed by parsing response logs
    if "Pushed" not in [alert['status'] for alert in response if 'status' in alert.keys()]:
        raise Exception("Image {} was not pushed to {}".format(image_name, registry_url))


def untar(tar_path, extract_path=None):
    """Untar a tarball and return extraction path

    :param tar_path: path of tarball
    :param extract_path: path of tar-extraction
    :return: path of where the tarball has been extracted to
    """
    if extract_path is None:
        tar_dir, tar_file = os.path.split(tar_path)
        tar_name, _ = os.path.splitext(tar_file)
        extract_path = os.path.join(tar_dir, tar_name)
    with tarfile.open(tar_path) as tar_handle:
        tar_handle.extractall(path=extract_path)
    return extract_path


def build_and_checkout(test_element, checkout_dir, cli, project):
    """Build and checkout specified element

    :param test_element: name of element to build and checkout
    :param checkout_dir: directory of checkout
    :param cli: handle to BuildStream
    :param project: directory of project
    """
    # build image
    result = cli.run(project=project, args=['build', test_element])
    result.assert_success()
    # checkout image
    os.makedirs(checkout_dir)
    result = cli.run(project=project, args=['artifact', 'checkout', '--directory', checkout_dir, test_element])
    result.assert_success()


def load_image(docker_client, path, artifact_name='image.tar'):
    """Load a Docker image to the Docker daemon. Equivalent to `docker load` command.

    :param docker_client: handle to Docker engine
    :param path: directory of image tarball
    :param artifact_name: name of image tarball
    :return: response from Docker daemon
    """
    image_path = str(os.path.join(path, artifact_name))
    with open(image_path, 'rb') as image_handle:
        response = docker_client.images.load(image_handle.read())
        # get first tag of first image
    return response


def get_image_tag(response):
    """Parse response from Docker daemon to get tag of image.

    :param response: response from Docker daemon
    :return: Tag of image
    """
    return response[0].tags[0]


def get_docker_host(docker_client):
    """Parse a DockerClient object to get the hostname of the Docker engine

    :param docker_client: handle to Docker engine
    :return: hostname of Docker engine
    """
    docker_host_url = docker_client.api.base_url.split('/')[-1]
    if ':' in docker_host_url:
        # strip port
        return docker_host_url.split(':')[0]
    else:
        return docker_host_url


def hash_digest(_file):
    """return hash digest of file

    :param _file: name of file to calculate hash of
    :return: hash digest of specified file
    """
    hash_algorithm = hashlib.sha256()
    with open(_file, 'rb') as file_handle:
        for block in _read_file_block(file_handle):
            hash_algorithm.update(block)
    return hash_algorithm.hexdigest()


def _read_file_block(file_handle, block_size=8192):
    """Yield chunk_size blocks of file

    :param file_handle: handle to file
    :param chunk_size: block size of file to be read
    :return: block of file
    """
    while True:
        data = file_handle.read(block_size)
        if not data:
            break
        else:
            yield data
