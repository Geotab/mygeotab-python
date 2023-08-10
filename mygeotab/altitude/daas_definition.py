
class DaasError:
    def __init__(self, error: dict):
        self.error = error
        self.code = self.error['code']
        self.domain = self.error['domain']
        self.message = self.error['message']

NOT_FULL_API_CALL_EXCEPTION = Exception("api return did not have all expected attributes, please retry again.")
class DaasResult:
    """DaasResult class, the base class for all results returned from calling our application from the gateway

    Attributes:
        call_result (dict):                 The result returned from the api call, this includes our gateway information.
        api_result (dict):                  The "apiResult" the result computed by altitude application.
        jobs (list):                        all the possible results returned by the altitude application call, normally it should always have the length of 1.
        job (dict):                         first result returned by the altitude application call (first element of jobs).
        daas_errors (list):                 possible errors list that happened on the gateway.
        api_result_errors  (list):          possible errors list that happened on the altitude application.
        api_result_error_message (str):     possible single error message that happened on the altitude application.
        api_result_error  (DaasError):      possible single error object that happened on the altitude application.
        errors (list):                      list of all the errors (gateway and altitude application) combined together.    
    """


    def __init__(self, call_result: dict):

        if not call_result:
            self.errors = [Exception("result is empty"), NOT_FULL_API_CALL_EXCEPTION]
            raise NOT_FULL_API_CALL_EXCEPTION

        self.call_result = call_result

        self.daas_errors = [DaasError(error) for error in self.call_result.get("errors", [])]
        self.errors = [
            Exception(error.message) for error in self.daas_errors
        ]


        if "apiResult" not in call_result:
            self.errors += [Exception("apiResult not present"), NOT_FULL_API_CALL_EXCEPTION]
            raise NOT_FULL_API_CALL_EXCEPTION

        self.api_result = self.call_result["apiResult"]
        self.jobs = self.api_result["results"]
        self.job = self.jobs[0]


        self.api_result_errors = [DaasError(error) for error in self.api_result.get("errors", [])]
        self.api_result_error_message = self.api_result.get("errorMessage", None)
        self.api_result_error = None


        
        
        self.errors += [
            Exception(error.message) for error in self.api_result_errors
        ]


        if "error" in self.api_result and self.api_result["error"]:   
            self.api_result_error = DaasError(self.api_result["error"])
            self.errors += [
                Exception(self.api_result_error.message) 
            ]

        if self.api_result_error_message and isinstance(self.api_result_error_message, str) and len(self.api_result_error_message):   
            self.errors += [
                Exception(self.api_result_error_message) 
            ]
        elif self.api_result_error_message and isinstance(self.api_result_error_message, dict):   
            self.errors += [
                Exception(self.api_result_error_message["message"]) 
            ]


class DaasGetJobStatusResult(DaasResult):
    """DaasGetJobStatusResult class, the returned format for checking the status of the job

    Attributes:
        id (str):           the id of the job returned
        status (dict):      the status of the job
        state (str):        the state of the job (from the status object)
    """
    
    
    def __init__(self, call_result: dict):
        super().__init__(call_result)
        self.id = self.job['id']
        self.status = self.job.get("status", {'state': 'FAILED'})
        self.state = self.status.get("state", "FAILED")
    def has_finished(self):
        if self.state == 'DONE':
            return True
        elif self.state != 'FAILED':
            return False
        elif self.state == 'FAILED' and self.errors and len(self.errors) > 0:
            return False
        else:
            raise Exception("got to failed state with no error, please reach out.")
    


class DaasGetQueryResult(DaasResult):
    """DaasGetQueryResult class, the returned format for checking the result of the job

    Attributes:
        totalRows (str):            the id of the job returned
        rows (list):                the rows including the data
        pageToken (str):            the token of the page
    """
    
    
    def __init__(self, call_result: dict):
        super().__init__(call_result)
        self.total_rows = self.job.get('totalRows', None)
        self.rows = self.job.get('rows', None)
        self.page_token = self.job.get('pageToken', None)

    
