# AWS Strand Agent with Documentation Access

This project implements a CI/CD pipeline using AWS CloudFormation that runs a Strand agent with access to AWS documentation through an MCP server.

## Components

1. **CloudFormation Template**: Sets up the CI/CD pipeline with CodeCommit, CodeBuild, and CodePipeline
2. **Strand Agent**: Python-based agent that can access AWS documentation via MCP server
3. **Build Configuration**: Includes buildspec.yml for CodeBuild

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.11 or higher
- Strand framework
- MCP client for AWS documentation access

## Deployment

1. Deploy the CloudFormation template:

```bash
aws cloudformation create-stack \
  --stack-name strand-agent-pipeline \
  --template-body file://pipeline-template.yaml \
  --capabilities CAPABILITY_IAM
```

2. Clone the created CodeCommit repository:

```bash
git clone <repository-url>
```

3. Add the project files to the repository:

```bash
cp strand_agent.py buildspec.yml requirements.txt README.md <repository-directory>
cd <repository-directory>
git add .
git commit -m "Initial commit"
git push
```

## Agent Configuration

The Strand agent can be configured using a YAML configuration file. Example:

```yaml
model: gpt-4o
output_dir: output
tasks:
  - name: aws_documentation_search
    description: Search AWS documentation for specific topics
    parameters:
      search_phrase: string
      limit: integer
```

## Running Locally

To run the agent locally:

```bash
python strand_agent.py --config config.yaml --task aws_documentation_search --params '{"search_phrase": "CloudFormation best practices"}'
```

## Pipeline Execution

The pipeline will automatically trigger when code is pushed to the configured branch. The CodeBuild step will:

1. Install dependencies from requirements.txt
2. Run the Strand agent
3. Store the output artifacts

## AWS Documentation Access

The agent uses the MCP client to access AWS documentation through the following methods:

- `search_aws_documentation`: Search for documentation on specific topics
- `read_aws_documentation`: Read content from a specific documentation URL
- `get_aws_documentation_recommendations`: Get related documentation recommendations

## Output

Results from the agent are stored in the `output` directory as JSON files.
