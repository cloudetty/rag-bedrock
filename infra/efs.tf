resource "aws_security_group" "efs" {
  name        = "${local.project}-efs-sg"
  description = "Allows Open WebUI tasks to mount the EFS filesystem"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.open_webui.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${local.project}-efs-sg"
    Project = local.project
  }
}

resource "aws_efs_file_system" "open_webui" {
  encrypted        = true
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

}

resource "aws_efs_access_point" "open_webui" {
  file_system_id = aws_efs_file_system.open_webui.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/open-webui-data"

    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "0755"
    }
  }
}

resource "aws_efs_mount_target" "private" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.open_webui.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs.id]
}
