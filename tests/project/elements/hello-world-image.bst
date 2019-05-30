kind: docker_image

config:
  cmd: ['/hello']
  env: ['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin']
  repositories: ['hello-world:latest']
build-depends:
 - hello-world.bst
