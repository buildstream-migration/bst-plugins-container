kind: docker_image
description: creates an image out of three shell scripts

config:
  image-names:
  - bst-plugins-container-tests/multiple-build-deps-bst:latest
  timestamp: deterministic
build-depends:
- layer1.bst
- layer2.bst
- layer3.bst
