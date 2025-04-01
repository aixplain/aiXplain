# API Key Tests

This directory contains tests for the API Key functionality in the aiXplain SDK.

## Prerequisites

To run these tests, you need:

1. An admin API key with permissions to:
   - Create new API keys
   - Update existing API keys
   - Delete API keys
   - List API keys
   - View API key usage

2. Available API key slots:
   - The tests create and delete API keys during execution
   - Make sure you have at least one available slot for API key creation
   - The tests will fail if you've reached the maximum number of allowed API keys

