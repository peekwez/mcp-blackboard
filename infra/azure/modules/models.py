from dataclasses import dataclass

import pulumi_azure_native as azure


@dataclass
class AzureResources:
    resource_group: (
        azure.resources.ResourceGroup
    )  # This will hold the Azure Resource Group object
    virtual_network: azure.network.VirtualNetwork | None = None
    # Azure Virtual Network
    subnets: dict[str, azure.network.Subnet] | None = None  # List of Subnet objects
    network_security_groups: dict[str, azure.network.NetworkSecurityGroup] | None = None
    storage_account: azure.storage.StorageAccount | None = (
        None  # Storage Account object
    )
    key_vault: azure.keyvault.Vault | None = None  # Azure Key Vault
    openai: azure.cognitiveservices.Account | None = None  # Azure OpenAI service
    document_intelligence: azure.cognitiveservices.Account | None = None
    redis_cache: azure.redis.Redis | None = None
    container_registry: azure.containerregistry.Registry | None = None
    user_identity: azure.managedidentity.UserAssignedIdentity | None = None
    kubernetes_cluster: azure.containerservice.ManagedCluster | None = None
