from datetime import datetime
import os
import tarfile

import pytest

from tests.utils import build_and_checkout, untar, load_image, get_image_tag, hash_digest

READ_WRITE_USER_PERMISSION = 0o775
DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'project'
)


@pytest.mark.datafiles(DATA_DIR)
def test_correct_checksum_docker_image(cli, datafiles, tmp_path):
    test_element = 'multiple-deps.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')

    build_and_checkout(test_element, checkout_dir, cli, project)
    extract_path = untar(os.path.join(checkout_dir, 'image.tar'))

    # check config file is correctly named
    config_json = [file for file in os.listdir(extract_path)
                   if file.endswith(".json") and file != "manifest.json"][0]
    assert config_json == "{}.json".format(hash_digest(os.path.join(extract_path, config_json)))

    # check each directory is correctly named
    for layer in os.listdir(extract_path):
        if os.path.isdir(layer):
            assert os.path.basename(layer) == hash_digest(os.path.join(layer, 'layer.tar'))


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_single_build_dep_docker_image(cli, docker_client, datafiles, tmp_path):
    test_element = 'hello-world-image.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')
    hello_exec = os.path.join(project, 'files', 'hello-world-image-fs', 'hello')

    # need to reset permission as copying files into `DATA_DIR` changes permissions
    os.chmod(hello_exec, READ_WRITE_USER_PERMISSION)

    build_and_checkout(test_element, checkout_dir, cli, project)
    tag = get_image_tag(load_image(docker_client, checkout_dir))

    # compare output of docker run
    output = docker_client.containers.run(tag).decode('utf-8')
    with open(os.path.join(project, 'files', 'hello-world_output.txt')) as expected_output:
        assert output == expected_output.read()

    _check_meta_data(docker_client, tag)


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_multiple_deps_docker_image(docker_client, cli, datafiles, tmp_path):
    test_element = 'multiple-deps.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')

    build_and_checkout(test_element, checkout_dir, cli, project)
    tag = get_image_tag(load_image(docker_client, checkout_dir))
    _check_meta_data(docker_client, tag)

    image_attrs = docker_client.images.get(tag).attrs
    assert len(image_attrs['RootFS']['Layers']) == 3
    _test_no_file_duplication(_get_layer_files(untar(os.path.join(checkout_dir, 'image.tar'))))


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_nested_deps_docker_image(docker_client, cli, datafiles, tmp_path):
    test_element = 'nested-deps.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')

    build_and_checkout(test_element, checkout_dir, cli, project)
    tag = get_image_tag(load_image(docker_client, checkout_dir))
    _check_meta_data(docker_client, tag)

    image_attrs = docker_client.images.get(tag).attrs
    assert len(image_attrs['RootFS']['Layers']) == 2
    _test_no_file_duplication(_get_layer_files(untar(os.path.join(checkout_dir, 'image.tar'))))


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_diamond_deps_docker_image(docker_client, cli, datafiles, tmp_path):
    test_element = 'diamond-deps.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')

    build_and_checkout(test_element, checkout_dir, cli, project)
    tag = get_image_tag(load_image(docker_client, checkout_dir))
    _check_meta_data(docker_client, tag)

    image_attrs = docker_client.images.get(tag).attrs
    assert len(image_attrs['RootFS']['Layers']) == 2

    # assert that there is no file duplication
    layer_files = _get_layer_files(untar(os.path.join(checkout_dir, 'image.tar')))
    _test_no_file_duplication(layer_files)


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_nested_overwrite_docker_image(docker_client, cli, datafiles, tmp_path):
    test_element = 'nested-overwrite.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')
    container_fs_export_dir = os.path.join(str(tmp_path), 'fs_extract')
    exported_tar = os.path.join(container_fs_export_dir, 'image.tar')
    os.makedirs(container_fs_export_dir)

    build_and_checkout(test_element, checkout_dir, cli, project)
    tag = get_image_tag(load_image(docker_client, checkout_dir))
    _check_meta_data(docker_client, tag)

    image_attrs = docker_client.images.get(tag).attrs
    assert len(image_attrs['RootFS']['Layers']) == 2

    # assert that file is indeed overwritten
    extract_path = untar(os.path.join(checkout_dir, 'image.tar'))
    assert _get_number_of_file_duplications(_get_layer_files(extract_path)) == 2

    # check overwritten file is content is as expected
    container = docker_client.containers.create(tag, command='/bin/sh')
    with open(exported_tar, 'wb+') as tar_handle:
        for chunk in container.export():
            tar_handle.write(chunk)
    with tarfile.open(exported_tar) as tar_handle:
        tar_handle.extractall(path=container_fs_export_dir)

    try:
        with open(os.path.join(container_fs_export_dir, 'layer1', 'hello.txt')) as produced_file:
            with open(os.path.join(project, 'files', 'layers', 'layer2', 'hello.txt')) as actual_file:
                assert produced_file.read() == actual_file.read()
    except FileNotFoundError:
        assert False


@pytest.mark.docker
@pytest.mark.datafiles(DATA_DIR)
def test_share_layers_docker_image(docker_client, cli, datafiles, tmp_path):
    """
        We have the following dependency graphs:

        (1) multiple-deps.bst
            |-> layer1.bst
            |-> layer2.bst
            |-> layer3.bst

        (2) nested-deps.bst -> layer2-nest.bst -|
            |                                   V
            |------------------------->layer1.bst

        Test that both images share the layer associated with layer1.bst
    """
    test_element1 = 'nested-overwrite.bst'
    test_element2 = 'multiple-deps.bst'
    project = str(datafiles)
    checkout_dir = os.path.join(str(tmp_path), 'checkout')
    checkout_dir1 = os.path.join(checkout_dir, 'test1')
    checkout_dir2 = os.path.join(checkout_dir, 'test2')

    build_and_checkout(test_element1, checkout_dir1, cli, project)
    build_and_checkout(test_element2, checkout_dir2, cli, project)

    tag1 = get_image_tag(load_image(docker_client, checkout_dir1))
    tag2 = get_image_tag(load_image(docker_client, checkout_dir2))

    fs1 = docker_client.images.get(tag1).attrs['RootFS']['Layers']
    fs2 = docker_client.images.get(tag2).attrs['RootFS']['Layers']

    # one of the layers should be shared
    assert len(set(fs1).intersection(set(fs2))) == 1


def _get_layer_files(extract_path):
    layer_files = []
    for layer in os.listdir(extract_path):
        if os.path.isdir(os.path.join(extract_path, layer)):
            with tarfile.open(os.path.join(extract_path, layer, 'layer.tar')) as tar_handle:
                layer_files.append(tar_handle.getmembers())
    # extract file name from tar_info
    return [set([member.name for member in tar_info]) for tar_info in layer_files]


def _get_number_of_file_duplications(layer_files):
    duplicated_files = set()
    for i, layer_a in enumerate(layer_files):
        for layer_b in layer_files[i + 1:]:
            duplicated_files |= layer_a & layer_b
    return len(duplicated_files)


def _test_no_file_duplication(layer_files):
    assert _get_number_of_file_duplications(layer_files) == 0


def _check_meta_data(docker_client, tag):
    # check meta-data of image
    image_attrs = docker_client.images.get(tag).attrs
    date_created = datetime.strptime(image_attrs['Created'], '%Y-%m-%dT%H:%M:%SZ')
    assert date_created.date() == datetime.now().date()
    assert image_attrs['Author'] == 'BuildStream docker_image plugin'
