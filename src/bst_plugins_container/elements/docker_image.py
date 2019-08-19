#  Copyright (C) 2019 Bloomberg Finance LP
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library. If not, see <http://www.gnu.org/licenses/>.
#
#  Authors:
#       Shashwat Dalal <sdalal29@bloomberg.net>
#

"""
docker_image - Produce Docker images
====================================
``docker_image`` element produces a Docker image based on its build
dependencies.

As the element creates a layer for each of its dependencies, the ``docker_image``
element *must* have at least one build dependency.  The element *must not* have
any run-time dependencies.

This plugin provides the following ``config`` options to modify
container-runtime configurations.

The default configuration is as such:
  .. literalinclude:: ../../../src/bst_plugins_container/elements/docker_image.yaml
     :language: yaml
"""

from datetime import datetime, date
import hashlib
import json
import os
import re
import tarfile

from buildstream import Element, Scope, ElementError
from buildstream.utils import move_atomic


class DockerElement(Element):
    BST_FORBID_SOURCES = True
    BST_FORBID_RDEPENDS = True
    BST_RUN_COMMANDS = False
    BST_VIRTUAL_DIRECTORY = False
    IMAGE_SPEC_VERSION = '1.2'
    LAYER_CONFIG_VERSION = '1.0'
    BST_FORMAT_VERSION = 1

    def configure(self, node):

        # validate yaml
        node.validate_keys([
            'exposed-ports',
            'env',
            'entry-point',
            'cmd',
            'volumes',
            'working-dir',
            'health-check',
            'image-names',
            'timestamp'
        ])

        health_check_node = node.get_mapping('health-check')
        health_check_node.validate_keys([
            'tests',
            'interval',
            'timeout',
            'retries'
        ])

        # populate config-variables as attributes
        self._exposed_ports = node.get_sequence('exposed-ports').as_str_list()
        self._env = node.get_sequence('env').as_str_list()
        self._entry_point = node.get_sequence('entry-point').as_str_list()
        self._cmd = node.get_sequence('cmd').as_str_list()
        self._volumes = node.get_sequence('volumes').as_str_list()
        self._working_dir = node.get_str('working-dir')
        self._timestamp = node.get_str('timestamp')
        self._health_check = {
            'Tests': health_check_node.get_sequence('tests', default=["NONE"]).as_str_list(),
            'Interval': health_check_node.get_int('interval', default=0),
            'Timeout': health_check_node.get_int('timeout', default=0),
            'Retries': health_check_node.get_int('retries', default=0)
        }
        self._image_names = node.get_sequence('image-names').as_str_list()

        # Reformat certain lists to dictionary as mandated by Docker image specification
        self._exposed_ports = {port: {} for port in self._exposed_ports}
        self._volumes = {volume: {} for volume in self._volumes}

        for i, image in enumerate(self._image_names):
            if ':' not in image:
                # enforce a default tag of 'latest'
                self._image_names[i] = "{}:latest".format(image)
        self._image_names = dict([repo.split(':', 1) for repo in self._image_names])

        # Set Headers
        self._author = 'BuildStream docker_image plugin'

    @property
    def _created(self):
        if self._timestamp == 'now':
            return "{}Z".format(datetime.utcnow().replace(microsecond=0).isoformat())
        elif self._timestamp == 'deterministic':
            from buildstream.utils import BST_ARBITRARY_TIMESTAMP
            return "{}T00:00:00Z".format(date.fromtimestamp(BST_ARBITRARY_TIMESTAMP).isoformat())
        else:
            return self._timestamp

    @property
    def _created_timestamp(self):
        datetime_object = datetime.strptime(self._created, "%Y-%m-%dT%H:%M:%SZ")
        return datetime_object.timestamp()

    def preflight(self):
        # assert exposed ports are valid
        port_options = ['tcp', 'udp']
        for port in self._exposed_ports:
            if '/' in port:
                port, port_option = port.split('/', 1)
                if port_option not in port_options:
                    raise ElementError("{}: Invalid port option {}. Options include: {}"
                                       .format(self, port_option, port_options),
                                       reason='docker-invalid-port-option')
            if int(port) > 65535 or int(port) < 0:
                raise ElementError("{}: Invalid port number {}"
                                   .format(self, port),
                                   reason='docker-port-out-out-of-range')

        # In order to build a Docker image of something,
        # Docker Element will have to require at least one build dependency
        build_deps = list(self.dependencies(Scope.BUILD, recurse=False))
        if len(build_deps) < 1:
            raise ElementError("{}: {} element must have at least one build dependency"
                               .format(self, type(self).__name__),
                               reason="docker-bdepend-wrong-count")

        # check image names are valid
        # https://docs.docker.com/registry/spec/api/#overview
        repository_syntax = re.compile(r'([a-z0-9][._/-]?)+(:([a-z0-9][._/-]?)+)?')
        for image_name in self._image_names:
            if not repository_syntax.fullmatch(image_name):
                raise ElementError("{}: {} image name is not valid"
                                   .format(self, image_name),
                                   reason="docker-bdepend-wrong-count")

        # assert timestamp options are valid
        timestamp_options = ['now', 'deterministic']
        if self._timestamp not in timestamp_options:
            try:
                iso_format = "%Y-%m-%dT%H:%M:%Sz"
                datetime.strptime(self._timestamp, iso_format)
            except ValueError:
                # does not match specified format
                raise ElementError("{}: {} timestamp is not valid"
                                   .format(self, self._timestamp),
                               reason="docker-wrong-timestamp-format")

    def get_unique_key(self):
        return {
            "exposed-ports": self._exposed_ports,
            "env": self._env,
            "entry-point": self._entry_point,
            "cmd": self._cmd,
            "volumes": self._volumes,
            "working-dir": self._working_dir,
            "health-check": self._health_check,
            "image-names": self._image_names,
            "image-spec-version": self.IMAGE_SPEC_VERSION,
            "layer-config-version": self.LAYER_CONFIG_VERSION
        }

    def configure_sandbox(self, sandbox):
        pass

    def stage(self, sandbox):
        pass

    def assemble(self, sandbox):
        basedir = sandbox.get_directory()

        # where dependencies will be staged
        dep_dir = os.path.join(basedir, 'dependencies')
        # where layers will be built
        layer_dir = os.path.join(basedir, 'layers')
        # where final image will be produced
        image_dir = os.path.join(basedir, 'image')

        # TODO use virtual directory interface to be remote-execution compatible
        os.makedirs(dep_dir)
        os.makedirs(layer_dir)
        os.makedirs(image_dir)

        # `layer_digests[0]` is the base layer, `layer_digest[n]` is the nth layer from the bottom
        layer_digests = [self._create_layer(layer_path, layer_dir) for layer_path in
                         self._stage_layers(sandbox, dep_dir)]

        # create image level files
        image_id = self._create_image_config(layer_dir, layer_digests)
        self._create_repositories_file(layer_dir, layer_digests[0])
        self._create_manifest(layer_dir, layer_digests, image_id)

        with self.timed_activity('Pack Image', silent_nested=True):
            self._pack_image(layer_dir, image_dir)

        return '/image'

    def _stage_layers(self, sandbox, dep_dir):
        """stage dependencies to element sandbox

        :param sandbox: sandbox of `docker_image` element
        :param dep_dir: directory in sandbox where to stage dependencies
        :return: list of paths to where the layers have been staged
        """
        # keep track of visited nodes
        visited = set()
        for dependency in self.dependencies(Scope.BUILD, recurse=False):
            # turn each immediate build dependency into a layer
            dep_name = dependency.normal_name
            with self.timed_activity("Staging {} Layer".format(dep_name), silent_nested=False):
                # create intermediate checkout directory for layer
                layer_path = os.path.join(dep_dir, dep_name)
                os.makedirs(layer_path, exist_ok=True)
                parent_folder = os.path.basename(dep_dir)
                relative_path = os.path.join(parent_folder, dep_name)
                self._stage_layer(sandbox, relative_path, dependency, visited)
                yield layer_path

    def _stage_layer(self, sandbox, layer_path, element, visited):
        """stages all run-time dependencies of `element` in 'layer_path` according to a dfs traversal

        :param sandbox: sandbox of `docker_image` element
        :param layer_path: path to where stage artifact of element
        :param element: element attempting to be staged
        :param visited: elements that have already been staged
        :return:
        """
        if element not in visited:
            visited.add(element)
            # only interested in run time dependencies of immediate build dependencies
            for dependency in element.dependencies(Scope.RUN):
                self._stage_layer(sandbox, layer_path, dependency, visited)
            # add current element's diff-set
            element.stage_dependency_artifacts(sandbox, Scope.NONE, path=layer_path)

    def _pack_image(self, layer_dir, image_dir):
        """tars `layer_dir` to create the docker-image, which is then placed in `image_dir`

        :param layer_dir: location of all untared docker-image files
        :param image_dir: location to place tared docker-image
        """

        # Tar contents of output dir to generate image
        tar_name = os.path.join(image_dir, "image.tar")
        mode = 'w'
        with tarfile.TarFile.open(name=tar_name, mode=mode) as tar_handle:
            for f in os.listdir(layer_dir):
                tar_handle.add(os.path.join(layer_dir, f), arcname=f)

    def _create_repositories_file(self, outputdir, top_layer_digest):
        """creates a repository file which contains all of the image's tags

        :param outputdir: directory to place file
        :param top_layer_digest: top layer digest
        """
        repositories = {
            name: "{}:{}".format(tag, top_layer_digest)
            for name, tag in self._image_names.items()
        }

        self._save_json(repositories, os.path.join(outputdir, 'repositories'))

    def _create_manifest(self, outputdir, layer_digests, config_digest):
        """creates the image manifest

        :param outputdir: directory to place file
        :param layer_digests: list of layer digests
        :param config_digest: digest of image
        """
        manifest = [{
            'Config': "{}.json".format(config_digest),
            # ordered bottom-most to top-most layer
            "Layers": ["{}/layer.tar".format(layer_digest) for layer_digest in layer_digests],
            "RepoTags": ["{}:{}".format(name, tag) for name, tag in self._image_names.items()]
        }]

        self._save_json(manifest, os.path.join(outputdir, 'manifest.json'))

    def _create_image_config(self, outputdir, layer_digests):
        """creates image configuration file

        :param outputdir: directory to place
        :param layer_digests:
        :return: the hex-digest of the hash of the config (a.k.a. image digest)
        """

        image_config = {
            'created': self._created,
            'author': self._author,
            'config': {
                "ExposedPorts": self._exposed_ports,
                "Env": self._env,
                "Entrypoint": self._entry_point,
                "Cmd": self._cmd,
                "Volumes": self._volumes,
                "WorkingDir": self._working_dir,
                "HealthCheck": self._health_check,
            },
            'rootfs': {
                'diff_ids': [
                    "sha256:{}".format(layer_digest)
                    for layer_digest in layer_digests
                ],
                'type': 'layers'
            },
            'history': [
                {
                    "created": self._created,
                    "created_by": "BuildStream Docker Image Plugin"
                }
                for _ in layer_digests
            ]
        }

        tmp_image_config = os.path.join(outputdir, 'tmp')
        self._save_json(image_config, tmp_image_config)

        # calculate hash of image
        image_digest = self._hash_digest(tmp_image_config)
        final_image_config = os.path.join(outputdir, '{}.json'.format(image_digest))

        move_atomic(tmp_image_config, final_image_config)

        return image_digest

    def _create_layer(self, changeset_dir, layer_dir):
        """creates the following file structure in layer_dir for the layer specified in chageset_dir

                    ├── <hash_digest>
                        ├── VERSION
                        ├── json
                        └── layer.tar

                :param changeset_dir: change-set for particular layer
                :param layer_dir: directory where layer will be built
                :return: hash_digest of layer
        """
        with self.timed_activity('Create {} Layer'.format(os.path.basename(changeset_dir)), silent_nested=True):
            # Create layer tar
            tmp_layer_dir = os.path.join(layer_dir, 'tmp')
            os.makedirs(tmp_layer_dir, exist_ok=True)
            tar_name = os.path.join(tmp_layer_dir, 'layer.tar')
            mode = 'w'

            def set_tar_headers(tarinfo):
                tarinfo.mtime = self._created_timestamp
                tarinfo.uid = tarinfo.gid = 0
                return tarinfo

            with tarfile.TarFile.open(name=tar_name, mode=mode) as tar_handle:
                for root, directories, files in os.walk(changeset_dir):
                    rel_root = image_root = os.path.relpath(root, changeset_dir)
                    if rel_root == '.':
                        image_root = '/'
                    for file_ in sorted(files + directories):
                        path = os.path.join(changeset_dir, rel_root, file_)
                        image_path = os.path.join(image_root, file_)
                        tar_handle.add(path, arcname=image_path, filter=set_tar_headers, recursive=False)

            # Calculate hash
            hash_digest = self._hash_digest(tar_name)

            # Rename tmp folder to hash of layer.tar
            layer_directory = os.path.join(layer_dir, hash_digest)
            move_atomic(tmp_layer_dir, layer_directory)

            # Create VERSION file
            with open(os.path.join(layer_directory, 'VERSION'), "w+") as version_handle:
                version_handle.write(self.LAYER_CONFIG_VERSION)

            # Create json file
            v1_json = {
                'id': hash_digest,
                'created': self._created,
                'author': self._author,
                'checksum': "tarsum.v1+sha256:{}".format(hash_digest),
                'config': {
                    "ExposedPorts": self._exposed_ports,
                    "Env": self._env,
                    "EntryPoint": self._entry_point,
                    "Cmd": self._cmd,
                    "Volumes": self._volumes,
                    "WorkingDir": self._working_dir,
                }
            }

            self._save_json(v1_json, os.path.join(layer_directory, 'json'))

        return hash_digest

    def _hash_digest(self, file):
        """return hash digest of file

        :param file: name of file to calculate hash of
        :param algorithm: hash algorithm that wants to be used
        :return: hash digest of specified file
        """
        hash_algorithm = hashlib.sha256()
        with open(file, 'rb') as file_handle:
            for block in self._read_file_block(file_handle):
                hash_algorithm.update(block)
        return hash_algorithm.hexdigest()

    @staticmethod
    def _save_json(body, file_location):
        """creates file at `file_location` and writes `body` to the file

        :param body: payload
        :param file_location: path of file
        """
        with open(file_location, 'w+') as file_handle:
            # Order the json. This is because py35 does not preserve insertion order whilst >=py36 does.
            json.dump(body, file_handle, sort_keys=True)

    @staticmethod
    def _read_file_block(file_handle, block_size=8192):
        """yield chunk_size blocks of file

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


def setup():
    return DockerElement
