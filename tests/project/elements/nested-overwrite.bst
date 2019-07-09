kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - bst-plugins-container-tests/nested-overwrite-bst:latest
build-depends:
- layer2-overwrite.bst
- layer1.bst
