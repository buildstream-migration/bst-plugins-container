from buildstream import Element, Scope, ElementError
from buildstream.utils import _magic_timestamp
import os
import tarfile
from datetime import datetime
import hashlib
import json
from stat import *


class DockerElement(Element):
    # Building Docker images will not require any source code or data to be imported into build environment
    BST_FORBID_SOURCES = True

    # Will not require run-time dependencies as image will not be run
    BST_FORBID_RDEPENDS = True

    # Will not be running any programs within sandbox in order to make the Docker image
    BST_RUN_COMMANDS = False

    # This plugin has been modified to avoid the use of Sandbox.get_directory
    BST_VIRTUAL_DIRECTORY = False

    def configure(self, node):

        self.config_vars = {
            'exposed_ports': list,
            'env': list,
            'entrypoint': list,
            'cmd': list,
            'volumes': list,
            'working_dir': str,
            'healthcheck': {
                'tests': list,
                'interval': int,
                'timeout': int,
                'retries': int
            },
            'repositories': list
        }

        # validate yaml
        self.node_validate(node, [self._snake_case_to_kebab_case(attr) for attr in self.config_vars.keys()])

        # populate config-variables as attributes
        self._parse_yaml(node)

        # Reformat certain lists to dictionary as mandated by Docker image specification
        self.exposed_ports = {port: {} for port in self.exposed_ports}
        self.volumes = {volume: {} for volume in self.volumes}
        self.repositories = {repo[0]: repo[1] for repo in [repo.split(':') for repo in self.repositories]}

        # Set Headers
        self.created = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        self.author = 'Buildtream docker_image plugin'

    def _parse_yaml(self, node):
        """
        ALWAYS USE API NOT INNER METHODS
        :param node:
        """

        for variable, expected_type in self.config_vars.items():
            if type(expected_type) is dict:
                inner_node = self.node_get_member(node, dict, self._snake_case_to_kebab_case(variable))
                setattr(self, variable, self._parse_dict_node_member(inner_node, expected_type))
            else:
                setattr(self, variable, self.node_get_member(node, expected_type,
                                                             self._snake_case_to_kebab_case(variable), None))

    def _parse_dict_node_member(self, node, config):
        parsed_dict = {}
        for variable, expected_type in config.items():
            if type(expected_type) is dict:
                # recurse
                inner_node = self.node_get_member(node, dict, self._snake_case_to_kebab_case(variable))
                parsed_dict[variable] = self._parse_dict_node_member(inner_node, expected_type)
            else:
                parsed_dict[variable] = \
                    self.node_get_member(node, expected_type, self._snake_case_to_kebab_case(variable), None)
        return parsed_dict

    def _snake_case_to_CamelCase(self, string):
        return ''.join(word.capitalize() for word in string.split('_'))

    def _snake_case_to_kebab_case(self, string):
        return '-'.join(string.split('_'))

    def preflight(self):
        # assert exposed ports are valid
        port_options = ['tcp', 'udp']
        for port in self.exposed_ports:
            if '/' in port:
                [port, port_option] = port.split('/')
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
        # fixme: for now assume there is only one build dep.
        build_deps = list(self.dependencies(Scope.BUILD, recurse=False))
        if len(build_deps) != 1:
            raise ElementError("{}: {} element must have at least one build dependency"
                               .format(self, type(self).__name__),
                               reason="docker-bdepend-wrong-count")

    def get_unique_key(self):
        return {attr: getattr(self, attr) for attr in self.config_vars.keys()}

    def configure_sandbox(self, sandbox):
        pass

    def stage(self, sandbox):
        pass

    def assemble(self, sandbox):

        basedir = sandbox.get_directory()
        inputdir = os.path.join(basedir, 'input')
        outputdir = os.path.join(basedir, 'tmp')
        imagedir = os.path.join(basedir, 'image')

        os.makedirs(inputdir, exist_ok=True)
        os.makedirs(outputdir, exist_ok=True)
        os.makedirs(imagedir, exist_ok=True)

        # Stage deps in the sandbox root
        with self.timed_activity('Staging dependencies', silent_nested=True):
            self.stage_dependency_artifacts(sandbox, Scope.BUILD, path='/input')

        # `layer_digest[0]` is the base layer, `layer_digest[n]` is the nth layer from the bottom
        layer_digests = []

        with self.timed_activity('Creating Layer', silent_nested=True):
            layer_digests.append(self._create_layer(inputdir, outputdir))

        with self.timed_activity('Creating Image Configuration', silent_nested=True):
            image_id = self._create_image_config(outputdir, layer_digests)

        with self.timed_activity('Create Repository File', silent_nested=True):
            self._create_repositories_file(outputdir, layer_digests[0])

        with self.timed_activity('Create Manifest', silent_nested=True):
            self._create_manifest(outputdir, layer_digests, image_id)

        with self.timed_activity('Pack Image', silent_nested=True):
            self._pack_image(outputdir, imagedir)

        return '/image'

    def _pack_image(self, outputdir, imagedir):
        """ tars `outputdir` to create the docker-image, which is then placed in `image_dir`

        :param outputdir: location of all untared docker-image files
        :param imagedir: location to place tared docker-image
        """

        # Tar contents of output dir to generate image
        tar_name = os.path.join(imagedir, "image.tar")
        mode = 'w'
        with tarfile.TarFile.open(name=tar_name, mode=mode) as tar_handle:
            for f in os.listdir(outputdir):
                tar_handle.add(os.path.join(outputdir, f), arcname=f)

    def _create_repositories_file(self, outputdir, top_layer_digest):
        """ creates a repository file which contains all of the image's tags

        :param outputdir:
        :param top_layer_digest:
        """

        repositories = {}
        for name, tag in self.repositories.items():
            repositories[name] = tag + ":" + top_layer_digest.split(':')[1]

        self._save_json(repositories, os.path.join(outputdir, 'repositories'))

    def _create_manifest(self, outputdir, layer_digests, config_digest):
        """ creates the image manifest

        :param outputdir:
        :param layer_digests:
        :param config_digest:
        """
        manifest = [{
            'Config': config_digest + ".json",
            # ordered bottom-most to top-most layer
            "Layers": [layer_digest.split(':')[1] + "/layer.tar" for layer_digest in layer_digests],
            "RepoTags": [name + ":" + tag for name, tag in self.repositories.items()]
        }]

        self._save_json(manifest, os.path.join(outputdir, 'manifest.json'))

    def _create_image_config(self, outputdir, layer_digests):
        """ creates image configuration file

        :param outputdir: directory to place
        :param layer_digests:
        :return: the hex-digest of the hash of the config (a.k.a. image digest)
        """

        image_config = {
            'created': self.created,
            'author': self.author,
            'config': {
                self._snake_case_to_CamelCase(attr): getattr(self, attr)
                for attr in self.config_vars.keys()
                if attr not in {'repositories'}
            },
            'rootfs': {
                'diff_ids': layer_digests,
                'type': 'layers'
            }
        }

        tmp_image_config = os.path.join(outputdir, 'tmp')
        self._save_json(image_config, tmp_image_config)

        # calculate hash of image
        image_digest = self._hash_digest(tmp_image_config)[1]
        final_image_config = os.path.join(outputdir, image_digest + '.json')

        os.rename(tmp_image_config, final_image_config)

        return image_digest

    def _create_layer(self, rfs_dir, output_dir):
        """creates the following file structure for the provided rfs_dir at the output_dir

                    ├── <hash_digest>
                        ├── VERSION
                        ├── json
                        └── layer.tar

                :param rfs_dir: root file system that wan
                :param output_dir: directory to place created layer sub-directory
                :return: hash_digest of layer
        """
        # todo deal with duplications between layers when dealing with more than one layer

        # Create layer tar
        tmp_layer_dir = os.path.join(output_dir, 'tmp')
        os.makedirs(tmp_layer_dir, exist_ok=True)
        tar_name = os.path.join(tmp_layer_dir, 'layer.tar')
        mode = 'w'

        def set_tar_headers(tarinfo):
            tarinfo.uname = tarinfo.gname = 'buildstream'
            tarinfo.mtime = _magic_timestamp
            return tarinfo

        with tarfile.TarFile.open(name=tar_name, mode=mode) as tar_handle:
            for f in os.listdir(rfs_dir):
                tar_handle.add(os.path.join(rfs_dir, f), arcname=f, recursive=True, filter=set_tar_headers)

        # Calculate hash
        hash_algorithm, hash_digest = self._hash_digest(tar_name)

        # Rename tmp folder to hash of layer.tar
        layer_directory = os.path.join(output_dir, hash_digest)
        os.rename(tmp_layer_dir, layer_directory)

        # Create VERSION file
        with open(os.path.join(layer_directory, 'VERSION'), "w+") as version_handle:
            version_handle.write('1.0')

        # Create json file
        v1_json = {
            'id': hash_digest,
            'created': self.created,
            'author': self.author,
            'checksum': "tarsum.v1+" + hash_algorithm + ":" + hash_digest,
            'config': {
                self._snake_case_to_CamelCase(attr): getattr(self, attr)
                for attr in self.config_vars.keys()
                if attr not in {'health_check', 'repositories'}
            }
        }

        self._save_json(v1_json, os.path.join(layer_directory, 'json'))

        return hash_algorithm + ":" + hash_digest

    def _hash_digest(self, file, algorithm='sha256'):
        """ return hash digest of file

        :param file: name of file to calculate hash of
        :param algorithm: hash algorithm that wants to be used
        :return: hash digest of specified file
        """
        if algorithm not in hashlib.algorithms_available:
            # todo raise proper exception
            raise Exception
        hash_algorithm = getattr(hashlib, algorithm)()
        with open(file, 'rb') as file_handle:
            for block in self._read_file_block(file_handle):
                hash_algorithm.update(block)
        return algorithm, hash_algorithm.hexdigest()

    @staticmethod
    def _save_json(body, file_location):
        """creates file at `file_location` and writes `body` to the file

        :param body:
        :param file_location:
        """
        with open(file_location, 'w+') as file_handle:
            json.dump(body, file_handle)

    @staticmethod
    def _read_file_block(file_handle, block_size=8192):
        """ yield chunk_size blocks of file

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
