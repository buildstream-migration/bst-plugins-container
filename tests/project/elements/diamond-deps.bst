kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - bst-plugins-container-tests/diamond-deps-bst:this-is-a-tag
build-depends:
- layer2-nested.bst
- layer3-nested.bst
