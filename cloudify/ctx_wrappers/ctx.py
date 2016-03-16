#!/usr/bin/env python

import subprocess
import json
import shlex


def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.
    Backported from Python 2.7 as it's implemented as pure python on stdlib.
    >>> check_output(['/usr/bin/python', '--version'])
    Python 2.6.2
    """
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output


def unicode_to_string(text):
    if isinstance(text, unicode):
        return text.encode('ascii', 'ignore')
    if isinstance(text, list):
        return [unicode_to_string(a) for a in text]
    if isinstance(text, dict):
        return dict((unicode_to_string(key), unicode_to_string(
                    value)) for key, value in text.iteritems())
    return text


class CtxLogger(object):
    def _logger(self, message, level):
        cmd = ['ctx', 'logger', level, message]
        return check_output(cmd)

    def debug(self, message):
        return self._logger(level='debug', message=message)

    def info(self, message):
        return self._logger(level='info', message=message)

    def warn(self, message):
        return self._logger(level='warn', message=message)

    def error(self, message):
        return self._logger(level='error', message=message)


# TODO: set immutable properties here.
class CtxNodeProperties(object):
    def __init__(self, relationship_type=None):
        self.relationship_type = relationship_type

    def __getitem__(self, property_name):
        cmd = ['ctx', '-j', 'node', 'properties', property_name]
        if self.relationship_type:
            cmd.insert(2, self.relationship_type)
        result = json.loads(check_output(cmd))
        return unicode_to_string(result)

    def get(self, property_name, returns=None):
        try:
            return self.__getitem__(property_name)
        except:
            return returns


class CtxNode(object):
    def __init__(self, relationship_type=None):
        self.relationship_type = relationship_type

    def _node(self, prop):
        cmd = ['ctx', '-j', 'node', prop]
        result = json.loads(check_output(cmd))
        return unicode_to_string(result)

    @property
    def properties(self):
        return CtxNodeProperties(self.relationship_type)

    @property
    def id(self):
        return self._node('id')

    @property
    def name(self):
        return self._node('name')

    @property
    def type(self):
        return self._node('type')


class CtxInstanceRuntimeProperties(object):
    def __init__(self, relationship_type=None):
        self.relationship_type = relationship_type

    def __getitem__(self, property_name):
        cmd = ['ctx', '-j', 'instance', 'runtime_properties', property_name]
        if self.relationship_type:
            cmd.insert(2, self.relationship_type)
        result = json.loads(check_output(cmd))
        return unicode_to_string(result)

    def get(self, property_name, returns=None):
        return self.__getitem__(property_name) or returns

    def __setitem__(self, property_name, value):
        cmd = ['ctx', 'instance', 'runtime_properties', property_name,
               value if isinstance(value, (basestring, str, unicode))
               else '@"{0}"'.format(value)]
        if self.relationship_type:
            cmd.insert(1, self.relationship_type)
        return check_output(cmd)


class CtxNodeInstance(object):
    def __init__(self, relationship_type=None):
        self.relationship_type = relationship_type

    def _instance(self, prop):
        cmd = ['ctx', '-j', 'instance', prop]
        if self.relationship_type:
            cmd.insert(2, self.relationship_type)
        result = json.loads(check_output(cmd))
        return unicode_to_string(result)

    @property
    def runtime_properties(self):
        return CtxInstanceRuntimeProperties(self.relationship_type)

    @property
    def host_ip(self):
        return self._instance('host_ip')

    @property
    def id(self):
        return self._instance('id')

    @property
    def relationships(self):
        return self._instance('relationships')


class CtxRelationshipInstance(object):
    def __init__(self, relationship_type):
        self.relationship_type = relationship_type

    @property
    def instance(self):
        return CtxNodeInstance(self.relationship_type)

    @property
    def node(self):
        return CtxNode(self.relationship_type)


class Ctx(object):
    def __init__(self):
        self._logger = CtxLogger()
        self._node = CtxNode()
        self._instance = CtxNodeInstance()
        self._target = CtxRelationshipInstance('target')
        self._source = CtxRelationshipInstance('source')

    def __call__(self, command_ref):
        ctx_command = shlex.split(command_ref)
        ctx_command.insert(0, 'ctx')
        return check_output(ctx_command)

    @property
    def node(self):
        return self._node

    @property
    def instance(self):
        return self._instance

    @property
    def target(self):
        return self._target

    @property
    def source(self):
        return self._source

    @property
    def logger(self):
        return self._logger

    def returns(self, data):
        cmd = ['ctx', '-j', 'returns', str(data)]
        return json.loads(check_output(cmd))

    # TODO: support kwargs for both download_resource and ..render
    def download_resource(self, source, destination=''):
        cmd = ['ctx', 'download-resource', source]
        if destination:
            cmd.append(destination)
        return check_output(cmd)

    def download_resource_and_render(self, source, destination='',
                                     params=None):
        cmd = ['ctx', 'download-resource-and-render', source]
        if destination:
            cmd.append(destination)
        if params:
            if not isinstance(params, dict):
                raise
            cmd.append(params)
        return check_output(cmd)


ctx = Ctx()
