kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - nested-overwrite-bst:latest
build-depends:
- layer2-overwrite.bst
