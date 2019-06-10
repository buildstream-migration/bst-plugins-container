kind: import
description: |
    Add second script
config:
  target: /layer3
sources:
  - kind: local
    path: ./files/layers/layer3
depends:
- layer1.bst
