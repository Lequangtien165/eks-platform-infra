# Full Workflow

## 1. Create Infrastructure

```powershell
cd A:\NoHomelessFuture\big_big_project\eks-platform-infra\environments\dev
terraform init
terraform plan
terraform apply
terraform output
```

Expected outputs:

- `vpc_id`
- `cluster_name`
- `cluster_endpoint`
- public and private subnet IDs

## 2. Build And Push The App Image

```powershell
cd A:\NoHomelessFuture\big_big_project\sample-app-gitops
docker build -t sample-app:0.1.0 .\app

aws ecr get-login-password --region ap-southeast-1 --profile nhf-project | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com

docker tag sample-app:0.1.0 <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/sample-app:0.1.0
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-southeast-1.amazonaws.com/sample-app:0.1.0
```

## 3. Bootstrap Platform Components

Run Ansible from WSL/Linux:

```bash
cd /mnt/a/NoHomelessFuture/big_big_project/automation/ansible
ansible-playbook bootstrap-platform.yml
```

If IRSA for AWS Load Balancer Controller does not exist yet:

```bash
ansible-playbook bootstrap-platform.yml \
  -e manage_aws_lbc_irsa_with_eksctl=true \
  -e aws_lbc_policy_arn=arn:aws:iam::<AWS_ACCOUNT_ID>:policy/AWSLoadBalancerControllerIAMPolicy
```

## 4. Verify Argo CD

```powershell
kubectl get pods -n argocd
kubectl get applications -n argocd
```

Port-forward Argo CD:

```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open:

```text
https://localhost:8080
```

Get the initial admin password:

```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String((kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}")))
```

## 5. Verify Dev Through ingress-nginx

```powershell
kubectl get pods -n ingress-nginx
kubectl get ingress -n dev
curl.exe -H "Host: sample-app-dev.local" http://<INGRESS_NGINX_ADDRESS>/
```

You can also test dev by port-forwarding:

```powershell
kubectl port-forward svc/sample-app -n dev 8081:80
```

Open:

```text
http://localhost:8081
```

## 6. Verify Prod Through AWS ALB

```powershell
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
kubectl get ingress -n prod
kubectl describe ingress sample-app -n prod
```

Test without owning a domain:

```powershell
curl.exe -H "Host: sample-app-prod.local" http://<ALB_DNS_NAME>/
```

Expected response:

```json
{"message":"sample-app is running","docs":"/docs","health":"/health","ready":"/ready","metrics":"/metrics","info":"/api/info"}
```

## 7. Clean Up Platform Resources Before Terraform Destroy

Delete ingress resources first so controllers can clean up AWS load balancers:

```powershell
kubectl delete application sample-app-dev sample-app-prod -n argocd --ignore-not-found
kubectl delete ingress sample-app -n dev --ignore-not-found
kubectl delete ingress sample-app -n prod --ignore-not-found
```

Wait until AWS load balancers are removed, then uninstall controllers:

```powershell
helm uninstall aws-load-balancer-controller -n kube-system
helm uninstall ingress-nginx -n ingress-nginx
kubectl delete namespace argocd ingress-nginx --ignore-not-found
```

## 8. Destroy Terraform Infrastructure

```powershell
cd A:\NoHomelessFuture\big_big_project\eks-platform-infra\environments\dev
terraform destroy
```
