kind: import
description: |
    Add second script
config:
  target: /layer1
sources:
  - kind: local
    path: ./files/layers/layer2
depends:
- layer1.bst
