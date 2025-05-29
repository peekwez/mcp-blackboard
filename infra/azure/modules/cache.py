import pulumi_azure_native as azure


def create_redis_service(
    resource_group: azure.resources.ResourceGroup, tags: dict[str, str]
) -> azure.redis.Redis:
    """
    Create Azure Redis Cache resource

    Args:
        resource_group(azure.resources.ResourceGroup): Azure resource group
        tags (Dict[str, str]): Resource tags

    Returns:
        azure.redis.Redis: Created Azure Redis Cache resource
    """
    # Create a Redis Cache name
    redis_cache = azure.redis.Redis(
        "redis",
        resource_group_name=resource_group.name,
        location=resource_group.location,
        disable_access_key_authentication=True,
        redis_version="7.2",
        sku={
            "name": azure.redis.SkuName.BASIC,
            "family": azure.redis.SkuFamily.C,
            "capacity": 1,
        },
        enable_non_ssl_port=False,
        minimum_tls_version="1.2",
        tags=tags,
    )

    return redis_cache
