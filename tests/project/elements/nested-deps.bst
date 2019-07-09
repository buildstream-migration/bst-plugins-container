kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - bst-plugins-container-tests/nested-deps-bst:latest
build-depends:
- layer2-nested.bst
- layer1.bst
