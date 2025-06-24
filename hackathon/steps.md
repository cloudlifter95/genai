`aws cloudformation create-stack \
  --stack-name strand-agent-pipeline \
  --template-body file://pipeline-template.yaml \
  --capabilities CAPABILITY_IAM`

