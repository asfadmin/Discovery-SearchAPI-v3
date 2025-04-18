# SearchAPI-v3

- Login to aws console using Kion
- Find the region that has the VPC and note account number, vpc_id, subnet_ids and security_group. Subnet_ids should be a comma separated list
- Get temp cli credentials from Kion and add them to your shell
- Run CDK bootstrap in region with the VPC using cdk-bootstrap-example.sh and filling in the account number, vpc_id, subnet_ids and security_group
- If not already created, make an GitHubActionsOidcProvider using the cdk/oidc/oidc-provider.yml template
- Create OIDC role using cloudformation template cdk/oidc/github-actions-oidc.yml. For 'ActionsRoleName' parameter put 'SearchAPIActionsOIDCRole'
- Create a github environment with params using the same values from the CDK bootstrap. AWS_ACCOUNT_ID, SECURITY_GROUP, SUBNET_IDS, VPC_ID
