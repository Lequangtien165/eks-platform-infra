# EKS GitOps Platform

This repository contains a compact production-style Kubernetes platform on AWS. It demonstrates infrastructure provisioning, application delivery, GitOps, image scanning, and a basic Kubernetes security baseline.

## What Is Included

- Terraform infrastructure for VPC, EKS, IAM roles, and node groups.
- A sample FastAPI application with health, readiness, metrics, and JSON logging.
- Docker image build and Trivy image scanning in GitHub Actions.
- Helm chart and environment-specific values for `dev` and `prod`.
- Argo CD Applications for GitOps deployment into EKS.
- Ansible automation to bootstrap post-cluster platform components.

## Repository Layout

```text
.github/workflows/ci.yml              GitHub Actions CI/CD workflow
eks-platform-infra/                   Terraform infrastructure
automation/ansible/                   EKS platform bootstrap playbook
sample-app-gitops/app/                Sample FastAPI application
sample-app-gitops/helm/sample-app/    Helm chart
sample-app-gitops/envs/               Dev/prod Helm values
sample-app-gitops/argocd/             Argo CD project and applications
```

## CI/CD Flow

1. GitHub Actions tests the FastAPI app import.
2. The workflow assumes an AWS IAM role through GitHub OIDC.
3. Docker builds the app image.
4. Trivy scans the image and fails on high or critical findings.
5. The image is pushed to Amazon ECR.
6. The dev image tag is updated in GitOps values and pushed back to `main`.

GitHub Actions are pinned to full commit SHAs.

## Required GitHub Secrets

Configure these repository secrets before running the workflow:

```text
AWS_ACCOUNT_ID
AWS_GITHUB_ACTIONS_ROLE_ARN
```

`AWS_ACCOUNT_ID` is used to construct the private ECR registry URL without storing the account ID in this repository.

## Local Bootstrap Inputs

The Ansible bootstrap renders Argo CD manifests at runtime so private repository and ECR details do not need to be committed.

```bash
export AWS_ACCOUNT_ID="<aws-account-id>"
export GIT_REPO_URL="https://github.com/<owner>/<repo>.git"
ansible-playbook automation/ansible/bootstrap-platform.yml
```

Optionally override the full ECR repository URI:

```bash
export ECR_REPOSITORY_URI="<aws-account-id>.dkr.ecr.<region>.amazonaws.com/sample-app"
```

## Security Baseline

- No AWS account ID, IAM role ARN, access key, or token is committed intentionally.
- Application containers run as non-root.
- Pods disable service account token automounting.
- Containers drop Linux capabilities and disable privilege escalation.
- Root filesystem is configured read-only.
- Argo CD project source and namespace permissions are scoped.
- FastAPI docs and OpenAPI are disabled when `APP_ENV=prod`.
- Trivy blocks images with high or critical vulnerabilities.

## Access Model

The sample app is exposed through Kubernetes Ingress. Argo CD is not published publicly by default.

Use port-forwarding for temporary administrative access:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open:

```text
https://localhost:8080
```

Keeping Argo CD behind port-forwarding, VPN, or a private network boundary is safer than exposing it directly to the internet.

