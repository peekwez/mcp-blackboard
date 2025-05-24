from dataclasses import dataclass

import pulumi_azure_native as azure


@dataclass
class Storage:
    account: azure.storage.StorageAccount
    blob_container: azure.storage.BlobContainer


def create_storage_services(
    resource_group: azure.resources.ResourceGroup, tags: dict[str, str]
) -> Storage:
    """
    Create Azure Storage resources

    Args:
        resource_group (azure.resources.ResourceGroup): Azure resource group
        tags (Dict[str, str]): Resource tags

    Returns:
        Storage: Created Azure Storage resources
    """

    # Create an Azure Storage Account
    storage_account = azure.storage.StorageAccount(
        "sa",
        resource_group_name=resource_group.name,
        location=resource_group.location,
        enable_https_traffic_only=True,
        is_hns_enabled=True,
        is_sftp_enabled=True,
        sku={
            "name": azure.storage.SkuName.STANDARD_LRS,
        },
        kind=azure.storage.Kind.STORAGE_V2,
        tags=tags,
    )

    # Create a Blob Container
    blob_container = azure.storage.BlobContainer(
        "cnt",
        resource_group_name=resource_group.name,
        account_name=storage_account.name,
        public_access=azure.storage.PublicAccess.NONE,
        metadata=tags,
    )
    return Storage(
        account=storage_account,
        blob_container=blob_container,
    )
