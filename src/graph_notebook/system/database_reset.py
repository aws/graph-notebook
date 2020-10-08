from graph_notebook.request_param_generator.call_and_get_response import call_and_get_response
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator

SYSTEM_ACTION = 'system'


def initiate_database_reset(host, port, use_ssl, request_param_generator=DefaultRequestGenerator()):
    data = {
        'action': 'initiateDatabaseReset'
    }
    res = call_and_get_response('post', SYSTEM_ACTION, host, port, request_param_generator, use_ssl, data)
    return res.json()


def perform_database_reset(token, host, port, use_ssl, request_param_generator=DefaultRequestGenerator()):
    data = {
        'action': 'performDatabaseReset',
        'token': token
    }
    res = call_and_get_response('post', SYSTEM_ACTION, host, port, request_param_generator, use_ssl, data)
    return res.json()
