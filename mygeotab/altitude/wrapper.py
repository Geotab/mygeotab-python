import sys
import time
import logging
from .daas_definition import DaasGetQueryResult, DaasGetJobStatusResult, DaasResult, NOT_FULL_API_CALL_EXCEPTION
from ..api import API, DEFAULT_TIMEOUT


class AltitudeAPI(API):
    def __init__(
        self,
        username,
        password=None,
        database=None,
        session_id=None,
        server="my.geotab.com",
        timeout=DEFAULT_TIMEOUT,
        proxies=None,
        cert=None,
    ):
        """
        A wrapper around mygeotab API for altitude users.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :type username: str
        :param password: The password associated with the username. Optional if `session_id` is provided.
        :type password: str
        :param database: The database or company name. Optional as this usually gets resolved upon authentication.
        :type database: str
        :param session_id: A session ID, assigned by the server.
        :type session_id: str
        :param server: The server ie. my23.geotab.com. Optional as this usually gets resolved upon authentication.
        :type server: str or None
        :param timeout: The timeout to make the call, in seconds. By default, this is 300 seconds (or 5 minutes).
        :type timeout: float or None
        :param proxies: The proxies dictionary to apply to the request.
        :type proxies: dict or None
        :param cert: The path to client certificate. A single path to .pem file or a Tuple (.cer file, .key file).
        :type cert: str or Tuple or None
        :raise Exception: Raises an Exception if a username, or one of the session_id or password is not provided.
        """

        super().__init__(
            username=username,
            password=password,
            database=database,
            session_id=session_id,
            server=server,
            timeout=timeout,
            proxies=proxies,
            cert=cert,
        )
        _ = logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        


    def _call_api(
        self, service_name: str, function_name: str, function_parameters: dict
    ) -> dict:
        results = self.call(
            method="GetBigDataResults",
            serviceName=service_name,
            functionName=function_name,
            functionParameters=function_parameters,
        )
        return results



    def call_api(self, function_name: str, params: dict) -> dict :
        '''
        Supports getJobStatus calls, and getQueryResults calls. Retries in case of errors like connection rest.
        '''
        assert function_name in ["getJobStatus", "getQueryResults", "createQueryJob"]
        max_tries = 5
        for try_index in range(max_tries):
            try:
                call_result = self._call_api(
                    service_name=params["serviceName"],
                    function_name=function_name,
                    function_parameters=params["functionParameters"],
                )
                DaasResult(call_result)
                return call_result
            except Exception as e:
                if e == NOT_FULL_API_CALL_EXCEPTION:
                    if try_index == max_tries - 1:
                        raise e
                    else:
                        print(f"encountered error trying to parse to api response {str(call_result)}, retrying....")
                        time.sleep((try_index + 1)*10)
                else:
                    raise e

    def create_job(self, params: dict) -> dict:
        """
        creates the job with the given params.
        """
        try:
            results = self.call_api(
                function_name="createQueryJob",
                params=params,
            )
            errors = results.get("errors", [])
            if errors and len(errors) > 0:
                raise errors[0]
            return results["apiResult"]["results"][0]
        except Exception as e:
            logging.error(f"Exception: {e}")
            logging.error(f"error: error while creating job, results: {results}")
            raise e

    def check_job_status(self, params: dict) -> DaasGetJobStatusResult:
        """
        checks the status of a given job. jobId needs to be included in params.
        """
        call_result = self.call_api("getJobStatus", params)
        daas_status = DaasGetJobStatusResult(call_result)
        return daas_status

    def wait_for_job_to_complete(self, params: dict) -> dict:
        """
        waits for a job to finish running and returns the job. jobId needs to be included in params.
        """
        while True:
            try:
                daas_status = self.check_job_status(params)
                if daas_status.errors and len(daas_status.errors) > 0:
                    raise daas_status.errors[0]
                else:
                    if daas_status.has_finished():
                        break
                time.sleep(5)

                logging.info(f"waiting for results: {daas_status.job}")

            except Exception as e:
                logging.error(f"Exception: {e}")
                logging.error(f"error: error while waiting for job to complete, result: {daas_status.job}")
                raise e
        return daas_status.job



    def fetch_data(self, params: dict) -> dict:
        """
        fetch data for the given params. jobId needs to be included in params.
        """
        index = 1

        daas_status = self.check_job_status(params)
        if daas_status.errors and len(daas_status.errors) > 0 or (not daas_status.has_finished()):
            raise Exception("fetch data was called before job had finished correctly.")
        while index:
            try:
                call_result = self.call_api("getQueryResults", params)
                daas_result = DaasGetQueryResult(call_result)
                results = daas_result.job

                rows = daas_result.rows
                page_token = daas_result.page_token
                total_rows = daas_result.total_rows
                if index == 1:
                    logging.info(f"total number of rows: {total_rows}")

                params["functionParameters"]["pageToken"] = page_token
                yield {"data": [rows, total_rows, index], "errors": daas_result.errors}
                index += 1
                if not page_token:
                    index = None
                    yield
            except Exception as e:
                logging.error(f"Exception: {e}")
                logging.error(f"error: error while fetching data, results: {results}")
                index = None
                raise e

    def get_data(self, params: dict) -> list:
        """
        uses and iterates through fetch_data for the given params, and returns the combined data. jobId needs to be included in params.
        """
        data = []
        results_iterator = self.fetch_data(params)
        for data_page in results_iterator:
            try:
                if type(data_page) == str:
                    raise Exception("recieved error:", data_page)
                page = [] if data_page is None else data_page["data"][0]
                errors: list = None if data_page == None else data_page.get("errors", None)
                if errors and len(errors) > 0:
                    logging.error(f"got error when getting data: {errors[0]}")
                    raise errors[0]
                data.extend(page)
            except Exception as e:
                logging.error(f"error: error while combining data:: {e}")
                raise e
        return data
    
    def do(self, params: dict) -> list:
        """
        given the parameters, will call the request, wait on it to finish and return the combined data.
        """
        logging.info(f"creating job")
        job = self.create_job(params)
        logging.info(f"job created: {job}")
        params["functionParameters"]["jobId"] = job["id"]
        logging.info(f"checking the job status")
        results = self.wait_for_job_to_complete(params)
        logging.info(f"job finished: {results}")
        logging.info(f"gathering result")
        data = self.get_data(params)
        logging.info(f"data gathered")
        return data









    
