# Azure Native Python Pulumi Infrastructure

A modular Pulumi project for provisioning Azure resources for MCP Blackboard.

## Overview

This infrastructure is organized into separate modules for better maintainability:

- **Common Module** - Shared resources (Resource Group)
- **AI Services Module** - Azure OpenAI and Document Intelligence
- **Storage Services Module** - Azure Storage Account and Blob Container
- **Redis Module** - Azure Redis Cache

## Resources

The infrastructure includes:

- **Common Resources**:

  - `azure-native:resources:ResourceGroup` — a new resource group

- **AI Services**:

  - `azure-native:cognitiveservices:Account` (OpenAI) — Azure OpenAI service
  - `azure-native:cognitiveservices:Account` (FormRecognizer) — Document Intelligence service

- **Storage Services**:

  - `azure-native:storage:StorageAccount` — a storage account for blob storage
  - `azure-native:storage:BlobContainer` — a blob container for document storage

- **Redis Service**:
  - `azure-native:cache:Redis` — Azure Redis Cache for caching

## Outputs

After deployment, the following outputs are available:

- `resource_group_name` - The name of the resource group
- `storage_account_name` - The name of the storage account
- `storage_primary_key` - The primary access key for the storage account
- `blob_container_name` - The name of the blob container
- `openai_endpoint` - The endpoint URL for the Azure OpenAI service
- `document_intelligence_endpoint` - The endpoint URL for Document Intelligence
- `redis_host` - The hostname for Redis Cache
- `redis_connection_string` - The connection string for Redis Cache

## Project Layout

```plaintext
.
├── __main__.py               # Main Pulumi program that imports all modules
├── modules/                  # Modules directory
│   ├── __init__.py           # Package initialization
│   ├── common.py             # Common resources (Resource Group)
│   ├── ai_services.py        # AI services (OpenAI, Document Intelligence)
│   ├── storage_services.py   # Storage services (Storage Account, Blob)
│   └── redis_service.py      # Redis service
├── .vscode/                  # VS Code settings
│   └── settings.json         # Run Ruff on save
├── .pre-commit-config.yaml   # Pre-commit hooks for linting
├── pyproject.toml            # Python project configuration
├── requirements.txt          # Project dependencies
├── Pulumi.yaml               # Project settings
├── Pulumi.dev.yaml           # Stack configuration
└── README.md                 # Documentation
```

## Prerequisites

- An Azure subscription with sufficient permissions
- Azure CLI installed and authenticated (`az login`)
- Python 3.8 or later
- Pulumi CLI installed

## Usage

1. Clone the repository and navigate to the infra directory

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks (optional):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. Deploy the stack:
   ```bash
   pulumi up
   ```

## Code Quality

This project is set up with the following code quality tools:

- **Ruff**: A fast Python linter and formatter that runs automatically on save
- **Mypy**: Static type checking
- **Pre-commit hooks**: Ensures code quality before commits

To install VS Code extensions for these tools:

```bash
code --install-extension charliermarsh.ruff
code --install-extension ms-python.mypy-type-checker
```

## Configuration

This project uses the following configuration:

- `azure-native:location` — Azure region to deploy resources. Defaults to `canadacentral`.

Set or override it with:

```bash
pulumi config set azure-native:location eastus
```

## Getting Help

- Pulumi Documentation: https://www.pulumi.com/docs/
- Azure Native Provider Reference: https://www.pulumi.com/registry/packages/azure-native/
