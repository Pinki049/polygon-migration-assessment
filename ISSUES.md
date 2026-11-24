Polygon-Migration Tool - Issues

## 1. Polygon API Errors

The application may face errors while sending requests to the Polygon API.

Some possible reasons are:

- Incorrect API key or API secret.
- Invalid problem ID or request parameters.
- Network issues while sending requests.
- Polygon returning an error response.

The `_make_request()` function handles these errors and raises an exception.

## 2. Test Cases Not Found

Sometimes, test cases may not be available for a problem.

The `get_all_test_cases()` function fetches test cases using `problem.tests`, `problem.testInput`, and `problem.testAnswer`.

If fetching a test case fails, its input and output are set to empty strings. During migration, test cases with missing input or output are skipped.

## 3. Redis Connection Issues

Redis is used to store test cases temporarily.

If Redis is not available or the connection details are incorrect, the application may fail to store or retrieve cached test cases.

The Redis connection uses the following settings:

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `REDIS_SSL`

The functions `store_test_cases_in_redis()` and `get_test_cases_from_redis()` handle Redis operations.

## 4. Test Cases Missing from Redis

Test cases may not be available in Redis because they have expired or were not stored successfully.

In this case, `migrate_to_azure_blob()` fetches the test cases again from Polygon and stores them in Redis.

The default cache expiry time is 30 minutes.

## 5. Custom Checker Compilation Failure

Some problems use a custom checker to verify the output of a submitted solution.

The `compile_custom_checker()` function uses `g++` to compile the checker source code.

Compilation may fail if:

- The `g++` compiler is not installed.
- The source code contains errors.
- The compilation process takes too long.

If compilation fails, the source code is uploaded to Azure as `custom_checker.cpp` instead of the compiled file.

## 6. Custom Checker File Not Found

The custom checker file may not be available through the Polygon API.

The `fetch_custom_checker_file()` function tries to fetch the file as a source file, a resource file, and then with the `.cpp` extension.

If the file cannot be fetched, the custom checker upload is skipped.

## 7. Azure Blob Storage Upload Errors

Uploading test cases or custom checkers to Azure may fail because of incorrect credentials, network issues, or storage-related errors.

The application uses `AzureBlobManager` from `problems/AzureTestcase.py` to handle Azure operations.

Errors during uploads are recorded in the logs.

## 8. Existing Test Cases Are Deleted Before Upload

Before uploading new test cases, the `migrate_to_azure_blob()` function deletes the existing test cases for that problem using:

```python
blob_manager.empty_blob(container_name, problem_id_for_naming)
```

If the new upload fails after the deletion, the existing test cases may no longer be available in Azure.

## 9. Temporary Files and Package Extraction

The `download_and_extract_package()` function downloads a ZIP package and extracts it to a temporary directory.

The package may fail to download or extract if the response is not a valid ZIP file or if `problem.html` is missing.

The temporary directory is removed after the operation is completed.

## 10. Logging and Debugging

The module uses Python's `logging` library to record errors and important operations.

These logs can help identify problems with API requests, Redis operations, compilation, and Azure uploads.

Some errors are handled inside individual functions, so the function may return an empty value or `None` instead of stopping the entire process.

## Conclusion

The main issues in this module are related to API requests, Redis caching, custom checker compilation, and Azure uploads.

These issues are handled through error checking, logging, and fallback operations wherever possible.