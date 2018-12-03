kind: script
description: |
  Docker source test

  Rather than make assertions about the whole Alpine Linux image, we
  just copy out the /etc/os-release file so that can be sanity checked.

depends:
- filename: dockerhub-alpine.bst
  type: build

config:
  commands:
  - mkdir -p %{install-root}/etc
  - cp /etc/os-release %{install-root}/etc/
