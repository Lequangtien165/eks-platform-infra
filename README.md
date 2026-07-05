# EKS GitOps Platform

Repo này là một bản platform Kubernetes thu nhỏ trên AWS. Mục tiêu chính là dựng được một luồng triển khai gần với thực tế: tạo hạ tầng bằng Terraform, chạy app trên EKS, deploy bằng GitOps, build image qua CI, scan bảo mật trước khi push, và giữ các thông tin nhạy cảm ra khỏi Git.

Đây không phải là một app business phức tạp. App chỉ đủ nhỏ để kiểm chứng toàn bộ pipeline hạ tầng và vận hành.

## Có Gì Trong Repo

- Terraform để tạo VPC, EKS, IAM role và managed node group.
- App mẫu viết bằng FastAPI, có `/health`, `/ready`, `/metrics` và log JSON.
- Dockerfile cho app.
- GitHub Actions để test, build image, scan bằng Trivy và push lên ECR.
- Helm chart cho app.
- Values riêng cho `dev` và `prod`.
- Argo CD Application để deploy app theo GitOps.
- Ansible playbook để bootstrap các thành phần sau khi EKS đã được tạo.

## Cấu Trúc Chính

```text
.github/workflows/ci.yml              CI/CD workflow
eks-platform-infra/                   Terraform cho AWS/EKS
automation/ansible/                   Playbook bootstrap platform
sample-app-gitops/app/                Source app FastAPI
sample-app-gitops/helm/sample-app/    Helm chart của app
sample-app-gitops/envs/               Values cho dev/prod
sample-app-gitops/argocd/             Argo CD project và applications
```

## Luồng CI/CD

Khi workflow chạy:

1. GitHub Actions checkout code và test app import được.
2. Workflow assume AWS IAM Role qua GitHub OIDC.
3. Docker build image cho app.
4. Trivy scan image, nếu có lỗi `HIGH` hoặc `CRITICAL` thì fail.
5. Image được push lên Amazon ECR.
6. Workflow cập nhật image tag cho môi trường `dev`.
7. Argo CD sync thay đổi từ Git về EKS.

Các GitHub Actions trong workflow được pin bằng full commit SHA để tránh rủi ro tag bị thay đổi.

## Secret Cần Có Trên GitHub

Vào GitHub repo settings và tạo các repository secrets:

```text
AWS_ACCOUNT_ID
AWS_GITHUB_ACTIONS_ROLE_ARN
```

`AWS_ACCOUNT_ID` dùng để dựng ECR registry URL trong workflow. Mình không commit account ID thật vào repo.

`AWS_GITHUB_ACTIONS_ROLE_ARN` là IAM Role cho GitHub Actions assume qua OIDC.

## Bootstrap Platform Bằng Ansible

Sau khi Terraform đã tạo EKS cluster, chạy Ansible để cài các thành phần platform như Argo CD, ingress controller và AWS Load Balancer Controller.

Trước khi chạy, export các biến cần thiết:

```bash
export AWS_ACCOUNT_ID="<aws-account-id>"
export GIT_REPO_URL="https://github.com/<owner>/<repo>.git"
ansible-playbook automation/ansible/bootstrap-platform.yml
```

Nếu muốn truyền thẳng ECR repository URI:

```bash
export ECR_REPOSITORY_URI="<aws-account-id>.dkr.ecr.<region>.amazonaws.com/sample-app"
```

Ansible sẽ render manifest Argo CD ở runtime. Nhờ vậy repo không cần chứa account ID, ECR URL thật hoặc repo URL cá nhân.

## Truy Cập Argo CD

Argo CD không được public ra internet mặc định. Cách an toàn hơn là dùng port-forward khi cần vào UI:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Sau đó mở:

```text
https://localhost:8080
```

Port-forward chỉ tạo đường hầm tạm thời từ máy local vào service trong cluster. Nó không mở Argo CD ra public.


## Lưu Ý Khi Làm Việc Với Repo

- Đừng dùng `git add .` nếu `git status` hiện nhiều file lạ do line ending.
- Không commit file local như `HOWTO.md` hoặc `README1.md`; hai file này đã được ignore.
- Nếu dùng chung repo giữa Windows và WSL, nên giữ line endings ổn định để tránh diff nhiễu.
- Nếu GitHub Actions fail, đọc log của step fail trước khi sửa hàng loạt.
