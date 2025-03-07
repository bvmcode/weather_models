

resource "null_resource" "create_ecr_repo" {
  provisioner "local-exec" {
    command = "bash ./scripts/build_and_push.sh"
    when = create
  }
}


resource "null_resource" "destroy_ecr_repo" {
  provisioner "local-exec" {
    command = "bash ./scripts/destroy.sh"
    when    = destroy
  }
}

