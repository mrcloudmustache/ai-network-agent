```mermaid
flowchart TD
    A[Marketing VPC 10.1.0.0/16] --> B[Transit Gateway]
    C[Sales VPC 10.5.0.0/16] --> B
    B --> D[Security VPC 10.100.0.0/16]
    D --> E[Firewall - Palo Alto]
    E --> B2[Transit Gateway Post Inspection]

    A --> F[Security Group Marketing]
    C --> G[Security Group Sales]
    E --> H[Firewall Policy - Allow RDP]
```