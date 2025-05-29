# type: ignore
import pulumi

# Import modules
from modules.common import create_common_resources
from modules.network import create_network_services

# Get project and stack names
project: str = pulumi.get_project()
stack: str = pulumi.get_stack()

# Define common tags
tags: dict[str, str] = {
    "project": project,
    "stack": stack,
    "environment": stack,
}


resource_group = create_common_resources(
    location="canadacentral",
    tags=tags,
)
network = create_network_services(
    resource_group=resource_group,
    location=resource_group.location.get(),
    tags=tags,
)
# storage = create_storage_services(
#     resource_group=resource_group,
#     tags=tags,
# )
