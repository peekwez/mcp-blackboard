from dataclasses import dataclass

import pulumi_azure_native as azure


@dataclass
class Network:
    vnet: azure.network.VirtualNetwork
    subnets: dict[str, azure.network.Subnet]
    sgs: dict[str, azure.network.NetworkSecurityGroup]


def create_network_services(
    resource_group: azure.resources.ResourceGroup,
    location: str,
    tags: dict[str, str],
) -> Network:
    """
    Create Azure Network resources

    Args:
        resource_group (azure.resources.ResourceGroup): Azure resource group
        location (str): Azure location (e.g., "canadacentral")
        tags (Dict[str, str]): Resource tags

    Returns:
        Network: Created Azure Network resources
    """

    # Create an Azure Virtual Network
    vnet = azure.network.VirtualNetwork(
        "vnet",
        resource_group_name=resource_group.name,
        location=location,
        address_space={"address_prefixes": ["10.0.0.0/16"]},
        tags=tags,
    )

    sgs = {
        "store": azure.network.NetworkSecurityGroup(
            "store-sg",
            resource_group_name=resource_group.name,
            location=location,
            security_rules=[
                azure.network.SecurityRuleArgs(
                    name="allow-https",
                    description="Allow HTTPS",
                    priority=1010,
                    direction=azure.network.SecurityRuleDirection.INBOUND,
                    access=azure.network.Access.ALLOW,
                    protocol=azure.network.SecurityRuleProtocol.TCP,
                    source_port_range="*",
                    destination_port_range="443",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
            ],
            tags=tags,
        ),
        "cache": azure.network.NetworkSecurityGroup(
            "cache-sg",
            resource_group_name=resource_group.name,
            location=location,
            security_rules=[
                azure.network.SecurityRuleArgs(
                    name="allow-redis-ssl",
                    description="Allow Redis SSL",
                    priority=1000,
                    direction=azure.network.SecurityRuleDirection.INBOUND,
                    access=azure.network.Access.ALLOW,
                    protocol=azure.network.SecurityRuleProtocol.TCP,
                    source_port_range="*",
                    destination_port_range="6380",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                )
            ],
            tags=tags,
        ),
        "vault": azure.network.NetworkSecurityGroup(
            "vault-sg",
            resource_group_name=resource_group.name,
            location=location,
            security_rules=[
                azure.network.SecurityRuleArgs(
                    name="allow-keyvault-https",
                    description="Allow Key Vault HTTPS",
                    priority=1000,
                    direction=azure.network.SecurityRuleDirection.INBOUND,
                    access=azure.network.Access.ALLOW,
                    protocol=azure.network.SecurityRuleProtocol.TCP,
                    source_port_range="*",
                    destination_port_range="443",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
            ],
            tags=tags,
        ),
        "webapp": azure.network.NetworkSecurityGroup(
            "webapp-sg",
            resource_group_name=resource_group.name,
            location=location,
            security_rules=[
                azure.network.SecurityRuleArgs(
                    name="allow-http",
                    description="Allow HTTP",
                    priority=1000,
                    direction=azure.network.SecurityRuleDirection.INBOUND,
                    access=azure.network.Access.ALLOW,
                    protocol=azure.network.SecurityRuleProtocol.TCP,
                    source_port_range="*",
                    destination_port_range="80",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
                azure.network.SecurityRuleArgs(
                    name="allow-https",
                    description="Allow HTTPS",
                    priority=1010,
                    direction=azure.network.SecurityRuleDirection.INBOUND,
                    access=azure.network.Access.ALLOW,
                    protocol=azure.network.SecurityRuleProtocol.TCP,
                    source_port_range="*",
                    destination_port_range="443",
                    source_address_prefix="*",
                    destination_address_prefix="*",
                ),
            ],
            tags=tags,
        ),
    }

    # Create subnets
    subnets = {
        "store": azure.network.Subnet(
            "store",
            resource_group_name=resource_group.name,
            virtual_network_name=vnet.name,
            address_prefix="10.0.1.0/24",
            service_endpoints=[
                azure.network.ServiceEndpointPropertiesFormatArgs(
                    service="Microsoft.Storage",
                )
            ],
        ),
        "cache": azure.network.Subnet(
            "cache",
            resource_group_name=resource_group.name,
            virtual_network_name=vnet.name,
            address_prefix="10.0.2.0/24",
            service_endpoints=[
                azure.network.ServiceEndpointPropertiesFormatArgs(
                    service="Microsoft.Cache",
                )
            ],
        ),
        "vault": azure.network.Subnet(
            "vault",
            resource_group_name=resource_group.name,
            virtual_network_name=vnet.name,
            address_prefix="10.0.3.0/24",
            service_endpoints=[
                azure.network.ServiceEndpointPropertiesFormatArgs(
                    service="Microsoft.KeyVault",
                )
            ],
        ),
        "webapp": azure.network.Subnet(
            "webapp",
            resource_group_name=resource_group.name,
            virtual_network_name=vnet.name,
            address_prefix="10.0.4.0/24",
            delegations=[
                azure.network.DelegationArgs(
                    actions=[
                        "Microsoft.Network/virtualNetworks/subnets/action",
                    ],
                    name="webapp-delegation",
                    service_name="Microsoft.Web/serverfarms",
                )
            ],
        ),
    }

    return Network(
        vnet=vnet,
        subnets=subnets,
        sgs=sgs,
    )
