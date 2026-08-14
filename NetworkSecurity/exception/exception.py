import sys
from NetworkSecurity.logging.logger import logging


class NetworkSecurityException(Exception):

    def __init__(self, error_message, error_detail):
        self.error_message = error_message

        _, _, exc_tb = error_detail.exc_info()

        self.lineno = exc_tb.tb_lineno
        self.file_name = exc_tb.tb_frame.f_code.co_filename

    def __str__(self):
        return "Error occurred in python script name [{0}] line number [{1}] error message [{2}]".format(
            self.file_name,
            self.lineno,
            self.error_message
        )

if __name__ == '__main__':
    try:
        logging.info("Enter the try block")

        a = 1 / 0

        print("This will not be printed", a)

    except Exception as e:
        logging.info("Enter the except block")
        raise NetworkSecurityException(e, sys)

