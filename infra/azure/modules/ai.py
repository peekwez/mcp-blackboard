# from typing import Any

# import pulumi_azure_native as azure


# def create_ai_services(
#     resource_group: azure.resources.ResourceGroup, tags: dict[str, str]
# ) -> dict[str, Any]:
#     """
#     Create Azure AI Services resources

#     Args:
#         resource_group (azure.resources.ResourceGroup): The resource group to
#             create the resources in.
#         tags (Dict[str, str]): Tags to apply to the resources.

#     Returns:
#         Dict[str, Any]: A dictionary containing the created resources.
#     """

#     # Create Document Intelligence (Form Recognizer) service
#     document_intelligence = azure.cognitiveservices.Account(
#         "document-intelligence",
#         resource_group_name=resource_group.name,
#         location=resource_group.location,
#         sku={
#             "name": "S0",
#             "tier": azure.cognitiveservices.SkuTier.STANDARD,
#         },
#         kind="FormRecognizer",
#         tags=tags,
#     )

#     # Create Azure OpenAI service
#     openai = azure.cognitiveservices.Account(
#         "openai",
#         resource_group_name=resource_group.name,
#         location=resource_group.location,
#         sku={
#             "name": "S0",
#             "tier": azure.cognitiveservices.SkuTier.STANDARD,
#         },
#         kind="OpenAI",
#         tags=tags,
#     )
#     openai_model = azure.cognitiveservices.Deployment(
#         "openai-model",
#         resource_group_name=resource_group.name,
#         account_name=openai.name,
#         deployment_name="gpt-4o",
#         model_id="gpt-4o",
#         tags=tags,
#     )

#     # Return the created resources
#     return (document_intelligence, openai, openai_model)
