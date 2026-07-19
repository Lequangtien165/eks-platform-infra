from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECR, EKS
from diagrams.aws.network import ALB, InternetGateway, NATGateway, VPC
from diagrams.aws.security import IAMRole
from diagrams.generic.compute import Rack
from diagrams.k8s.compute import Deploy, Pod
from diagrams.k8s.ecosystem import Helm
from diagrams.k8s.network import Ingress, Service
from diagrams.k8s.podconfig import Secret
from diagrams.onprem.ci import GithubActions
from diagrams.onprem.client import User
from diagrams.onprem.gitops import ArgoCD
from diagrams.onprem.iac import Ansible, Terraform
from diagrams.onprem.network import Nginx
from diagrams.onprem.vcs import Github

graph_attr = {
    "fontsize": "22",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
    "nodesep": "0.7",
    "ranksep": "1.0",
}

node_attr = {
    "fontsize": "12",
}

edge_attr = {
    "fontsize": "10",
    "color": "#374151",
}

with Diagram(
    "EKS GitOps Platform Architecture",
    filename="eks_gitops_platform",
    outformat=["png", "svg"],
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    developer = User("Developer")

    with Cluster("GitHub"):
        repo = Github("Repo\napp + Helm + Argo CD manifests")
        actions = GithubActions("GitHub Actions\nTest, build, scan, push")

    terraform = Terraform("Terraform\nVPC + EKS")
    ansible = Ansible("Ansible Bootstrap")

    with Cluster("AWS Account\nap-southeast-1"):
        ecr = ECR("Amazon ECR\nsample-app images")
        oidc_role = IAMRole("IAM Role\nGitHub OIDC")

        with Cluster("VPC\ncreated by Terraform"):
            igw = InternetGateway("Internet Gateway")
            nat = NATGateway("NAT Gateway")

            with Cluster("Public Subnets"):
                alb = ALB("AWS ALB\nprod traffic")
                ingress_nginx = Nginx("ingress-nginx\ndev traffic")

            with Cluster("Private Subnets"):
                eks = EKS("EKS Cluster\nnhf-eks-dev")
                nodes = Rack("Managed\nNode Group")

                with Cluster("Kubernetes Platform"):
                    argo = ArgoCD("Argo CD\nGitOps controller")
                    aws_lbc = ALB("AWS Load Balancer\nController")
                    helm = Helm("Helm chart\nsample-app")

                    with Cluster("namespace: dev"):
                        dev_ingress = Ingress("Ingress\nsample-app-dev.local")
                        dev_service = Service("Service\nsample-app:80")
                        dev_deploy = Deploy("Deployment\nsample-app")
                        dev_pods = Pod("FastAPI Pods")

                    with Cluster("namespace: prod"):
                        prod_ingress = Ingress("Ingress\nsample-app-prod.local")
                        prod_service = Service("Service\nsample-app:80")
                        prod_deploy = Deploy("Deployment\nsample-app")
                        prod_pods = Pod("FastAPI Pods")

                    helm_values = Secret("Helm values\ndev/prod")

    end_user = User("User / Tester")

    developer >> Edge(label="push code") >> repo
    repo >> Edge(label="trigger") >> actions
    actions >> Edge(label="assume role") >> oidc_role
    actions >> Edge(label="push image") >> ecr
    actions >> Edge(label="update dev values.yaml") >> repo

    terraform >> Edge(label="provision") >> VPC("AWS VPC")
    terraform >> Edge(label="create cluster") >> eks
    eks >> nodes
    igw >> alb
    nat >> nodes

    ansible >> Edge(label="install") >> argo
    ansible >> Edge(label="install") >> ingress_nginx
    ansible >> Edge(label="install") >> aws_lbc

    repo >> Edge(label="watch GitOps repo") >> argo
    argo >> Edge(label="sync Helm release") >> helm
    helm >> helm_values
    helm_values >> dev_ingress
    helm_values >> prod_ingress

    ecr >> Edge(label="pull image") >> dev_pods
    ecr >> Edge(label="pull image") >> prod_pods

    end_user >> Edge(label="dev HTTP\nHost: sample-app-dev.local") >> ingress_nginx
    ingress_nginx >> dev_ingress >> dev_service >> dev_deploy >> dev_pods

    end_user >> Edge(label="prod HTTP\nHost: sample-app-prod.local") >> alb
    aws_lbc >> Edge(label="manages") >> alb
    alb >> prod_ingress >> prod_service >> prod_deploy >> prod_pods
