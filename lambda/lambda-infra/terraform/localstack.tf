terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.54.0"
    }
  }
}

provider "aws" {
  region                      = "ap-southeast-2"
  access_key                  = "fake"
  secret_key                  = "fake"

  skip_credentials_validation = true
  skip_requesting_account_id  = true

  endpoints {
    dynamodb = "http://localstack:4566"
    lambda   = "http://localstack:4566"
  }
}

resource "aws_dynamodb_table" "table_1" {
  name        = "table_1"
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "ID"
  attribute {
    name = "ID"
    type = "S"
  }
   tags = {
    environment       = "dev"
  }
}

resource "aws_dynamodb_table_item" "dynamodb_schema_table_item" {
  for_each = local.tf_data
  table_name = aws_dynamodb_table.table_1.name
  hash_key   = "ID"
  item = jsonencode(each.value)
}

resource "aws_lambda_function" "counter" {
  function_name = "counter"
  filename      = "lambda.zip"
  role          = "fake_role"
  handler       = "main.handler"
  runtime       = "nodejs8.10"
  timeout       = 30
}
