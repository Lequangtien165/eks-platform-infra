# EKS Platform Bootstrap With Ansible

This playbook bootstraps Kubernetes platform components after Terraform has created the EKS cluster.

Terraform remains responsible for AWS infrastructure. Argo CD remains responsible for application state. Ansible only orchestrates the bootstrap steps that need to happen after the cluster exists.

## What It Does

- Updates local kubeconfig for the EKS cluster.
- Reads `vpc_id` from Terraform output.
- Installs or updates Argo CD.
- Installs or updates `ingress-nginx` for dev/lab ingress.
- Installs or updates AWS Load Balancer Controller for prod ALB ingress.
- Applies Argo CD project and app manifests.
- Prints ingress status.

## Prerequisites

Run this from WSL/Linux or another environment with Ansible available. Windows PowerShell can drive Terraform and kubectl, but Ansible itself is not natively supported on Windows as a control node.

Required CLIs:

```bash
aws
kubectl
helm
terraform
ansible-playbook
```

Optional when `manage_aws_lbc_irsa_with_eksctl=true`:

```bash
eksctl
```

## Run

From this directory:

```bash
ansible-playbook bootstrap-platform.yml
```

If AWS Load Balancer Controller IRSA has not already been created by Terraform or a previous `eksctl` run:

```bash
ansible-playbook bootstrap-platform.yml \
  -e manage_aws_lbc_irsa_with_eksctl=true \
  -e aws_lbc_policy_arn=arn:aws:iam::<AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy
```

## Access

Argo CD local UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Dev app through ingress-nginx:

```bash
kubectl get ingress -n dev
```

Prod app through AWS ALB:

```bash
kubectl get ingress -n prod
curl -H "Host: sample-app-prod.local" http://<ALB_DNS_NAME>/
```
