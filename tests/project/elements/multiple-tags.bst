kind: docker_image

description: Creates a hello-world image with multiple tags

build-depends:
- hello-world.bst

config:
  image-names:
  - bst-plugins-container-tests/multiple-tags/name1:tag1
  - bst-plugins-container-tests/multiple-tags/name1:tag2
  - bst-plugins-container-tests/multiple-tags/name2:tag1
  - bst-plugins-container-tests/multiple-tags/name2:tag2
  - bst-plugins-container-tests/multiple-tags/name3:tag6
