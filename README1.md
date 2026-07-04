# Production-Style Kubernetes Platform on AWS

## Summary

Xây một platform thu nhỏ trên AWS để deploy và vận hành 1 ứng dụng mẫu bằng `Terraform + EKS + Helm + ArgoCD + Prometheus/Grafana + Loki + security baseline`.

Mục tiêu của project không phải làm app phức tạp, mà là chứng minh năng lực `Cloud Infrastructure`, `Infrastructure as Code`, `Kubernetes operations`, `GitOps`, `observability`, và `security-aware deployment`.

Scope được chốt để hoàn thành trong 3-4 tuần với mức độ đủ mạnh cho CV:
- 1 EKS cluster
- 2 môi trường logic: `dev` và `prod` bằng config tách biệt, không cần 2 cluster riêng
- 1 ứng dụng mẫu dạng web API đơn giản
- GitOps cho app manifests
- Metrics, logs, alerts cơ bản
- Security baseline vừa đủ để nói chuyện tốt trong interview

## Exact Scope

### Kiến trúc chính
- AWS làm hạ tầng chính.
- Terraform provision:
  - `VPC`
  - `public/private subnets`
  - `NAT gateway` hoặc cost-optimized network option nếu cần giảm chi phí
  - `IAM roles`
  - `EKS cluster`
  - `managed node group`
  - `security groups`
  - `S3 bucket` cho Terraform backend
- Kubernetes layer:
  - `nginx ingress controller` hoặc `AWS Load Balancer Controller`
  - `cert-manager` là optional, chỉ làm nếu còn thời gian
  - `external-dns` bỏ khỏi v1 nếu chưa có domain
- GitOps:
  - `ArgoCD`
  - app deploy qua `Helm chart`
  - repo config theo kiểu `app-of-apps` đơn giản hoặc một app ArgoCD duy nhất
- Observability:
  - `kube-prometheus-stack` cho metrics và dashboards
  - `Loki + Promtail` cho logs
  - 2-3 alert rules cơ bản
- Security baseline:
  - `IRSA` cho workload cần quyền AWS
  - secrets không hardcode trong repo
  - network policy tối thiểu cho app namespace
  - container chạy non-root nếu app cho phép
  - image scan trong CI bằng `Trivy`
- CI:
  - GitHub Actions build image, scan image, push image
  - ArgoCD tự sync manifest hoặc Helm values sau khi tag image mới

### Ứng dụng mẫu
- Chọn 1 app đơn giản, không tự làm business logic phức tạp.
- Khuyến nghị:
  - `FastAPI` hoặc `Node.js` API rất nhỏ
  - có endpoint `/health`, `/ready`, `/metrics`
  - có log structured JSON
  - có biến môi trường config theo env
- App chỉ cần đủ để chứng minh:
  - containerization
  - ingress
  - scaling
  - monitoring
  - deployment lifecycle

### Những gì không làm trong v1
- Không làm service mesh
- Không làm multi-region
- Không làm autoscaling quá sâu ngoài HPA cơ bản
- Không làm full secret manager integration phức tạp nếu vượt thời gian
- Không làm 2 EKS cluster riêng cho dev/prod
- Không làm microservices nhiều service

## Implementation Blueprint

### 1. Repository structure
Tách thành 2 repo hoặc 1 mono-repo có 3 phần rõ ràng:
- `infra/`: Terraform cho AWS + EKS
- `platform/`: Helm/ArgoCD manifests cho ingress, monitoring, logging, ArgoCD
- `app/`: source app mẫu + Dockerfile + Helm chart hoặc chart riêng ở `platform/apps`

Khuyến nghị cho CV:
- Dùng 2 repo:
  - `eks-platform-infra`
  - `sample-app-gitops`
- Lý do:
  - thể hiện rõ separation of concerns
  - dễ giải thích GitOps model hơn trong interview

### 2. Terraform design
Thiết kế Terraform theo module-level đủ sạch, không over-engineer:
- `modules/vpc`
- `modules/eks`
- `modules/iam-irsa` nếu cần
- `environments/dev`
- `environments/prod`

Yêu cầu implementation:
- remote backend trên S3
- variables tách cho từng env
- outputs cho cluster name, region, VPC id, subnets
- naming convention nhất quán
- README ghi `terraform init/plan/apply/destroy`

Tradeoff đã chọn:
- `dev` và `prod` dùng cùng 1 cluster nhưng tách namespace, values, resource quota cơ bản
- vẫn giữ Terraform env separation để chứng minh environment management
- giảm cost mạnh hơn so với 2 cluster riêng

### 3. Kubernetes platform layer
Sau khi có cluster:
- cài `ArgoCD`
- cài ingress controller
- cài `kube-prometheus-stack`
- cài `Loki + Promtail`
- tạo namespaces:
  - `argocd`
  - `platform`
  - `dev`
  - `prod`

Yêu cầu:
- mọi platform component phải có manifest hoặc Helm values lưu trong git
- hạn chế click tay trong console
- ghi rõ bootstrap order:
  1. Terraform dựng infra
  2. kubeconfig vào cluster
  3. install ArgoCD bootstrap
  4. ArgoCD sync phần còn lại

### 4. GitOps workflow
Model triển khai:
- app source code push lên GitHub
- GitHub Actions:
  - test cơ bản
  - build Docker image
  - scan image bằng Trivy
  - push image lên registry
- update image tag trong repo GitOps hoặc dùng image updater nếu muốn, nhưng v1 nên đơn giản:
  - commit image tag mới vào Helm values của env
- ArgoCD detect drift và sync cluster

Chốt cho v1:
- không dùng image automation quá phức tạp
- ưu tiên quy trình rõ ràng, dễ demo, dễ giải thích

### 5. Observability
Metrics:
- dùng `kube-prometheus-stack`
- dashboard tối thiểu:
  - cluster health
  - node/pod CPU/memory
  - app request rate / latency nếu có metrics
- app expose `/metrics`

Logs:
- dùng `Loki + Promtail`
- app log JSON
- dashboard/log query demo được theo namespace và pod

Alerts:
- ít nhưng có giá trị:
  - pod restart tăng bất thường
  - high CPU hoặc memory app
  - app down / target unavailable
- có thể route alert tới email hoặc Telegram nếu dễ làm

### 6. Security baseline
Mục tiêu là “nói chuyện được như một platform-minded engineer”, không phải đạt compliance.
Làm các điểm sau:
- không commit secret plaintext
- dùng `Kubernetes Secret` sinh từ pipeline hoặc sealed/managed approach đơn giản nếu đủ thời gian
- service account riêng cho app
- `IRSA` nếu app cần gọi AWS service
- network policy giới hạn traffic trong namespace
- security context cho container:
  - `runAsNonRoot`
  - drop capabilities nếu phù hợp
- Trivy scan image trong CI
- README ghi rõ risk chưa xử lý trong v1

### 7. Demo scenarios phải có
Project chỉ mạnh nếu demo được các tình huống vận hành. Bắt buộc chuẩn bị:
- deploy app mới qua GitOps
- rollback về image/version cũ
- scale replicas
- xem dashboard metrics
- xem logs khi app lỗi
- trigger một alert mẫu
- chứng minh thay đổi infra qua Terraform plan/apply
- chứng minh tách config giữa `dev` và `prod`

## 4-Week Delivery Plan

### Week 1
- chốt kiến trúc, repo structure, naming
- dựng Terraform backend
- viết module VPC + EKS
- tạo cluster chạy được
- containerize app mẫu

### Week 2
- cài ingress controller
- cài ArgoCD
- deploy app qua Helm
- thiết lập namespace `dev` và `prod`
- hoàn thiện GitHub Actions build, scan, push image

### Week 3
- cài Prometheus/Grafana
- cài Loki/Promtail
- app expose metrics, logs chuẩn
- tạo dashboards và alert rules cơ bản

### Week 4
- thêm security baseline
- test rollback, failure scenarios, resource limits, HPA nếu còn thời gian
- viết tài liệu, chụp kiến trúc, quay demo ngắn
- tinh chỉnh CV bullet và GitHub README

## Deliverables

### GitHub deliverables
- repo infra với Terraform modules và README rõ ràng
- repo app/GitOps với Helm values theo env
- sơ đồ kiến trúc
- screenshots:
  - ArgoCD sync
  - Grafana dashboard
  - Loki logs
  - AWS resources
- demo video ngắn 3-5 phút

### CV-ready outcomes
Project này phải cho phép bạn viết được các bullet kiểu:
- Designed and provisioned a production-style AWS EKS platform using Terraform with reusable modules for VPC, IAM, and cluster resources.
- Implemented GitOps-based Kubernetes deployments with ArgoCD and Helm across isolated dev/prod environments.
- Built observability stack with Prometheus, Grafana, Loki, and alerting for cluster and application monitoring.
- Applied security best practices including IRSA, container image scanning, least-privilege service accounts, and Kubernetes network policies.

## Test Plan

- Terraform:
  - `plan` sạch cho từng env
  - apply thành công từ trạng thái trống
  - destroy thành công
- Kubernetes:
  - app reachable qua ingress
  - readiness/liveness probes hoạt động
  - rolling update không downtime rõ rệt
- GitOps:
  - đổi image tag trong git làm cluster sync đúng
  - drift bị ArgoCD phát hiện
- Observability:
  - metrics hiện trong Grafana
  - logs query được trong Loki
  - alert test kích hoạt đúng
- Security:
  - image scan chạy trong CI
  - pod chạy non-root
  - network policy không phá luồng hợp lệ nhưng chặn luồng không cần thiết

## Assumptions And Defaults

- Chọn `EKS` thay vì self-managed Kubernetes để CV tập trung vào platform engineering hơn là cluster bootstrapping.
- Chọn `ArgoCD` thay vì Flux vì dễ demo trực quan và phổ biến trong phỏng vấn.
- Chọn `1 cluster / 2 namespaces` thay vì `2 clusters` để giữ scope khả thi trong 3-4 tuần.
- Chọn `FastAPI` app đơn giản để effort dồn vào infra/platform thay vì business logic.
- Chọn security baseline vừa đủ thay vì secret/compliance stack đầy đủ.
- Nếu budget căng, có thể giảm một trong hai phần:
  - bỏ `prod` namespace riêng, chỉ giữ values tách biệt
  - bỏ logging stack, giữ metrics + alerts trước
