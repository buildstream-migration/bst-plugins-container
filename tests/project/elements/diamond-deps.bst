kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - diamond-deps-bst:latest
build-depends:
- layer2-nested.bst
- layer3-nested.bst
