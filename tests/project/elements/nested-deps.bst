kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - nested-deps-bst:latest
build-depends:
- layer2-nested.bst
