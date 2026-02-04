# =============================================================================
# Cluster Outputs
# =============================================================================

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.main.arn
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = aws_eks_cluster.main.version
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

# =============================================================================
# OIDC Outputs (for IRSA)
# =============================================================================

output "oidc_provider_arn" {
  description = "OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "oidc_provider_url" {
  description = "OIDC provider URL"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# =============================================================================
# Security Group Outputs
# =============================================================================

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_security_group.cluster.id
}

output "node_security_group_id" {
  description = "EKS node security group ID"
  value       = aws_security_group.node.id
}

# =============================================================================
# IAM Role Outputs
# =============================================================================

output "cluster_role_arn" {
  description = "EKS cluster IAM role ARN"
  value       = aws_iam_role.cluster.arn
}

output "node_role_arn" {
  description = "EKS node IAM role ARN"
  value       = aws_iam_role.node.arn
}

# =============================================================================
# VPC Outputs
# =============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

# =============================================================================
# kubectl Configuration
# =============================================================================

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${data.aws_region.current.name}"
}

output "kubeconfig" {
  description = "kubectl config as a yaml file"
  sensitive   = true
  value       = <<-KUBECONFIG
    apiVersion: v1
    kind: Config
    clusters:
    - cluster:
        server: ${aws_eks_cluster.main.endpoint}
        certificate-authority-data: ${aws_eks_cluster.main.certificate_authority[0].data}
      name: ${aws_eks_cluster.main.name}
    contexts:
    - context:
        cluster: ${aws_eks_cluster.main.name}
        user: ${aws_eks_cluster.main.name}
      name: ${aws_eks_cluster.main.name}
    current-context: ${aws_eks_cluster.main.name}
    users:
    - name: ${aws_eks_cluster.main.name}
      user:
        exec:
          apiVersion: client.authentication.k8s.io/v1beta1
          command: aws
          args:
          - eks
          - get-token
          - --cluster-name
          - ${aws_eks_cluster.main.name}
  KUBECONFIG
}
