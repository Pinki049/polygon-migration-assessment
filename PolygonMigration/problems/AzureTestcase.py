import os
import logging
from abc import ABC, abstractmethod
from azure.identity import UsernamePasswordCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ClientAuthenticationError

logger = logging.getLogger(__name__)


class BlobStorage(ABC):
    """
    Storage interface used by the migration flow.
    Any provider (Azure, S3, R2, GCS) can be added by implementing these methods.
    """

    @abstractmethod
    def upload_test_case(self, container_name, db_problem_id, test_number, input_data, output_data):
        """Upload the input and output files of one test case."""

    @abstractmethod
    def empty_blob(self, container_name, problem_id):
        """Delete every stored file of one problem."""


class AzureBlobManager(BlobStorage):
    """
    Azure Blob Storage implementation of BlobStorage.

    If AZURE_STORAGE_CONNECTION_STRING is set in the environment (or passed in),
    it is used for authentication. Otherwise the original username/password
    (Azure AD) login is used.
    """

    def __init__(self, account_url=None, tenant_id=None, client_id=None,
                 username=None, password=None, connection_string=None):
        self.account_url = account_url
        self.blob_service_client = None

        connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        try:
            if connection_string:
                logger.info("Connecting to Azure Blob Storage with a connection string...")
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                logger.info("BlobServiceClient created from connection string.")
            else:
                logger.info("Attempting to authenticate with Azure AD user credentials...")
                credential = UsernamePasswordCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    username=username,
                    password=password
                )
                self.blob_service_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
                logger.info("Authentication successful. BlobServiceClient created.")
        except ClientAuthenticationError as e:
            logger.warning(f"Authentication Failed: {e}")
            logger.warning("\nPlease check your credentials (username, password, tenant_id, client_id).")
            logger.warning("This method may not work if Multi-Factor Authentication (MFA) is enabled for the user.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during initialization: {e}")
            raise

    def upload_test_case(self, container_name, db_problem_id, test_number, input_data, output_data):
        input_blob_name = f"test_cases/{db_problem_id}/{test_number:02d}"
        output_blob_name = f"test_cases/{db_problem_id}/{test_number:02d}.a"
        try:
            input_blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=input_blob_name)
            input_blob_client.upload_blob(input_data.encode('utf-8'), overwrite=True)
            logger.info(f"Uploaded input for test #{test_number} to {input_blob_name}")
            output_blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=output_blob_name)
            output_blob_client.upload_blob(output_data.encode('utf-8'), overwrite=True)
            logger.info(f"Uploaded output for test #{test_number} to {output_blob_name}")
        except Exception as e:
            logger.error(f"Error uploading test case #{test_number}: {e}")

    def empty_blob(self, container_name, problem_id):
        prefix = f"test_cases/{problem_id}/"
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs_to_delete = [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
            for blob_name in blobs_to_delete:
                logger.info(f"Deleting blob: {blob_name}")
                container_client.delete_blob(blob_name)
            logger.info(f"Deleted {len(blobs_to_delete)} blobs for problem {problem_id} in container {container_name}.")
        except Exception as e:
            logger.error(f"Error deleting blobs for problem {problem_id}: {e}")