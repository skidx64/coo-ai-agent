# Lambda Function Configuration

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Attach Bedrock full access policy
resource "aws_iam_role_policy_attachment" "bedrock_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
  role       = aws_iam_role.lambda_role.name
}

# Lambda function
resource "aws_lambda_function" "api_handler" {
  filename         = "${path.module}/../coo-lambda.zip"
  function_name    = "${var.project_name}-api-handler-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "src.lambda_handler.handler"
  source_code_hash = filebase64sha256("${path.module}/../coo-lambda.zip")
  runtime         = var.lambda_runtime
  memory_size     = var.lambda_memory_size
  timeout         = var.lambda_timeout

  environment {
    variables = {
      ENVIRONMENT           = "aws"
      AI_PROVIDER          = "bedrock"
      RAG_PROVIDER         = "chromadb"
      BEDROCK_MODEL_ID     = var.bedrock_model_id
      BEDROCK_KB_ID        = var.bedrock_kb_id
      DATABASE_URL         = var.database_url
      TWILIO_ACCOUNT_SID   = var.twilio_account_sid
      TWILIO_AUTH_TOKEN    = var.twilio_auth_token
      TWILIO_PHONE_NUMBER  = var.twilio_phone_number
      SKIP_AUTH            = "true"
      DEMO_FAMILY_ID       = "1"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.bedrock_access
  ]
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = 7 # Keep logs for 7 days (cost optimization)
}
