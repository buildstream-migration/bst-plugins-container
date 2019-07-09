kind: docker_image
description: creates an image out of hello-world file system with added config
config:
  cmd:
   - /hello
  env:
  - PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  image-names:
  - bst-plugins-container-tests/hello-world-bst:latest
build-depends:
 - hello-world.bst
