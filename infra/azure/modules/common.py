"""
This module defines common Azure infrastructure resources
"""

import pulumi_azure_native as azure


def create_common_resources(
    location: str, tags: dict[str, str]
) -> azure.resources.ResourceGroup:
    """
    Create common Azure resources like resource group

    Args:
        location (str): Azure location (e.g., "canadacentral")
        tags (Dict[str, str]): Resource tags

    Returns:
        azure.resources.ResourceGroup: Created Azure Resource Group
    """

    # Create an Azure Resource Group
    resource_group = azure.resources.ResourceGroup("rg", location=location, tags=tags)

    # Return the created resources
    return resource_group
