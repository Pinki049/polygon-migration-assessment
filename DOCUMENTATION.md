Polygon-Migration Tool - Documentation 

1. Overview

This module connects the application with the Polygon API. It is used to get problem details, download problem files, fetch test cases, and move them to Azure Blob Storage.

Redis is used to save test cases temporarily so that the application does not have to fetch them from Polygon every time.

The main class used in this module is PolygonAPI.

2. Imports and Configuration

The module uses the following libraries:

hashlib, time, random, and string for generating API signatures.

requests for sending requests to Polygon.

json for handling JSON data.

os, sys, zipfile, tempfile, shutil, and subprocess for file handling and compilation.

redis for storing and retrieving test cases.

logging for tracking the operations.

The API credentials are taken from Django settings:

self.api_key = settings.POLYGON_API_KEY
self.api_secret = settings.POLYGON_API_SECRET

The Polygon API URL is:

API_URL = "https://polygon.codeforces.com/api/"

3. API Authentication and Requests

_generate_api_sig()

This function creates the signature required for Polygon API requests.

It adds the API key and current time to the request parameters. The parameters are sorted and converted into a string using urlencode().

A random six-character prefix is generated, and the final signature is created using SHA-512.

The function returns the signature and the time used in the request.

_make_request()

This function sends POST requests to Polygon.

It uses _generate_api_sig() to generate the required signature and sends the request using requests.post().

It checks the response and raises an error if the request fails or Polygon returns a failed status.

If expect_json=True, the response is parsed as JSON. Otherwise, the raw response text is returned.

_make_plain_request()

This function is used when the API response is plain text instead of JSON.

It calls _make_request() with expect_json=False.

4. Fetching Problem Information

The following functions are used to get information about a problem from Polygon.

Function

get_problem_info() : Fetches problem details using problem.info.

get_statements() : Fetches problem statements using problem.statements.

get_test_script() : Fetches the test script using problem.script.

get_test_cases() : Fetches test cases using problem.tests.

get_problem_files() : Fetches the list of files using problem.files.

get_file_content() : Fetches a particular file using problem.viewFile.

get_all_test_cases() : Fetches all test cases along with their input and output.

Some functions return an empty list, empty dictionary, or error message if the requested data cannot be fetched.

get_all_test_cases() 
This function fetches all test cases using problem.tests.

For every test case, it gets the input and output separately using: 
problem.testInput 
problem.testAnswer

It also stores information such as the test index, whether the test is manual, whether it is used in the problem statement, and its description.

If fetching a test case fails, its input and output are set to empty strings.

5. Downloading Problem Packages

download_and_extract_package()

This function downloads a problem package from Polygon and extracts the files.

It first fetches the problem information and available packages. It then selects the latest package matching the requested type, which is standard by default.

The package is downloaded using the problem.package API.

The downloaded data is checked to make sure it is a valid ZIP file. After extraction, the function searches for problem.html and reads its content.

The extracted files are stored in a temporary directory. The directory is removed after the operation is completed.

6. Custom Checker Handling

Some problems use a custom checker to verify the output of a submitted solution.

get_custom_checker_info()

This function uses the problem.checker API to check whether a problem has a custom checker.

If a custom checker is found, it returns its name and type.

fetch_custom_checker_file()

This function fetches the custom checker source code using problem.viewFile.

It first tries to fetch the file as a source file. If that fails, it tries the resource file type.

If the file is still not found, it tries adding the .cpp extension to the file name.

compile_custom_checker()

This function compiles the custom checker source code using g++.

The source code is saved as:

custom_checker.cpp

The compiler uses the following command:

g++ -std=gnu++17 -O2 -o <binary_file> <source_file>

On Windows, the compiled file is named custom_checker.exe. On other systems, it is named custom_checker.

The function returns the path of the compiled file if compilation is successful. Otherwise, it returns None.

The compiler is searched for using shutil.which('g++').

7. Uploading Custom Checkers to Azure

upload_custom_checker_to_azure()

This function fetches the custom checker from Polygon, compiles it, and uploads it to Azure Blob Storage.

It uses the AzureBlobManager class from:

problems/AzureTestcase.py

The compiled checker is uploaded to the following location:

test_cases/<problem_id_for_naming>/custom_checker.exe

On non-Windows systems, the file name is custom_checker instead of custom_checker.exe.

If compilation fails, the source code is uploaded instead:

test_cases/<problem_id_for_naming>/custom_checker.cpp

The function uses db_problem_id for naming the Azure files when it is provided. Otherwise, it uses the Polygon problem ID.

8. Redis Cache

Redis is used to store test cases temporarily.

The Redis connection details are taken from Django settings:

REDIS_HOST

REDIS_PORT

REDIS_PASSWORD

REDIS_SSL

store_test_cases_in_redis()

This function stores test cases in Redis.

Each test case is stored separately, along with its input, output, index, description, and sample information.

The Redis keys follow this format:

polygon_migration_test_cases_<polygon_id>_count
polygon_migration_test_cases_<polygon_id>_test_<index>

The default expiry time is 0.5 hours, which is 30 minutes.

get_test_cases_from_redis()

This function retrieves test cases from Redis using the Polygon problem ID.

It first gets the total number of test cases and then retrieves each test case separately.

If no test cases are found or an error occurs, it returns None.

clear_test_cases_from_redis()

This function removes all Redis keys related to a particular Polygon problem ID.

It uses the following key pattern:

polygon_migration_test_cases_<polygon_id>*

delete_problem_test_case_cache()

This function deletes cached test cases using the database problem ID.

It uses the following Redis key pattern:

oj_dev_with_redis_storage_test_cases_<db_problem_id>*

9. Migrating Test Cases to Azure Blob Storage

migrate_to_azure_blob()

This is the main function used to move test cases from Polygon to Azure Blob Storage.

The function first checks Redis for the test cases.

If the test cases are not available in Redis, it fetches them from Polygon using get_all_test_cases() and stores them in Redis for future use.

It then creates an AzureBlobManager instance and uploads the test cases to Azure.

Before uploading the new test cases, it deletes the existing test cases for that problem using:

blob_manager.empty_blob(container_name, problem_id_for_naming)

Only test cases that have both input and output are uploaded.

The upload is performed using:

blob_manager.upload_test_case(
    container_name,
    problem_id_for_naming,
    idx,
    input_data,
    output_data
)

After uploading the test cases, the function checks for a custom checker and uploads it if one is available.

10. Migration Workflow

The complete migration process works as follows:

The application provides the Polygon problem ID.

The module checks Redis for existing test cases.

If the test cases are not available, they are fetched from Polygon.

The fetched test cases are stored in Redis.

Existing test cases in Azure are deleted before the new ones are uploaded.

Test cases with both input and output are uploaded to Azure Blob Storage.

The custom checker is fetched and compiled if it exists.

The compiled checker or source code is uploaded to Azure.

The migration process is completed.

11. Logging and Error Handling

The module uses Python's logging library to track the main operations.

Logs are created for API requests, test case fetching, Redis operations, compilation, and Azure uploads.

Errors are handled in different functions to avoid stopping the entire process unnecessarily. For example, if a test case cannot be fetched, the function records the error and continues with the remaining test cases.

12. Conclusion

This module handles the complete process of fetching problem data from Polygon and moving test cases and custom checkers to Azure Blob Storage.

Redis helps avoid repeated API requests, while the Azure storage functions handle the upload of test cases and custom checkers.

The main purpose of this module is to make the test case migration process easier and reduce unnecessary requests to Polygon.


## User Flow :

The tool copies a problem from Polygon into our own database, and then uploads its test case files to cloud storage. 
For setup  install:
Python 3.12
PostgreSQL
Redis
Create an Azure storage account with a container called testcases. 
Keep all the keys and passwords are in a .env file including Polygon key and secret.

Server will run on : http://127.0.0.1:8000/
Terminal command : python manage.py runserver

{Login using Superuser email and password as only staff can login}

Create the problem on Polygon and enter the problem id on http://127.0.0.1:8000/ abd fetch problem.

{"Behind the scenes the app calls the Polygon API with my API key and secret, and pulls in the statement, the limits, and the test cases. Nothing has been saved yet."}

Set diffucalty level and add tags then click "Create/Update problem in database this will save problem and its details, like difficulty and tags, in our PostgreSQL database.

Click "Migrate tescases to Database" : This saves the test case information in our database tables.

Click "Migrate Test Cases to Azure." : Test cases were migrated to Azure Blob Storage successfully.

Open Azure container to verify the testcases. Inside is a test_cases folder, then a folder named after the database problem ID, for example 1.
There are 26 files: for each test, an input file, like 01, and an output file ending in .a, like 01.a. The input file has '1 2', and the output file has '3'. That matches the first test on Polygon, so the upload is correct.

To finish, here's the difference between the two kinds of migration. Saving to the database stores the information about the problem: its title, difficulty, tags, statement, and test case details. Uploading to Azure stores the actual input and output files, which can be large and are meant to be read when solutions are checked.

That's the full flow: fetch from Polygon, save to the database, save the test case details, and upload the files to storage.