# Deployment Instructions

Follow these steps to deploy the API client improvements to the server:

## 1. Connect to the Server

First, connect to your Linode server using SSH:

```bash
ssh root@your-server-ip
```

## 2. Navigate to the Project Directory

```bash
cd ~/marvin-memory/marvins-memory
```

## 3. Pull the Latest Changes

```bash
git fetch
git checkout api-client-improvements
```

## 4. Rebuild and Restart the Docker Container

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## 5. Verify the Deployment

Check that the container is running:

```bash
docker ps
```

And check the logs to make sure there are no errors:

```bash
docker logs marvins-memory_marvin_memory_1
```

## What Changed

1. **Added Pagination Support**:
   - The `/memories/` endpoint now supports pagination with `page` and `limit` parameters
   - The response includes pagination metadata (total count, total pages)

2. **Fixed Qdrant Filter Issues**:
   - Added better handling of filter formats for compatibility with the Qdrant server
   - Implemented fallback mechanisms when filters cause errors

3. **Added Metadata Support**:
   - Updated the `store_memory` method to accept a `metadata` parameter
   - This fixes the error in the tweet processor: `MemoryManager.store_memory() got an unexpected keyword argument 'metadata'`

4. **Client Examples**:
   - Added Python, JavaScript, and TypeScript client examples
   - These demonstrate how to properly connect to the API with pagination and error handling

## Troubleshooting

If you encounter any issues:

1. Check the Docker logs for error messages
2. Verify that the `api-client-improvements` branch was successfully checked out
3. Make sure the Docker container was rebuilt and restarted
4. If needed, you can manually apply the changes to the `src/memory/manager.py` file to add the `metadata` parameter
