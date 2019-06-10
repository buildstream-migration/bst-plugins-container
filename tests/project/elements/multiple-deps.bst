kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - multiple-build-deps-bst:latest
build-depends:
- layer1.bst
- layer2.bst
- layer3.bst
