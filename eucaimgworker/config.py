# (c) Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

import os
import httplib2
import boto
import boto.provider

DEFAULT_PID_ROOT = "/var/run/eucalyptus-imaging-worker"
DEFAULT_PIDFILE = os.path.join(DEFAULT_PID_ROOT, "eucalyptus-imaging-worker.pid")
CONF_ROOT = "/etc/eucalyptus-imaging-worker"
RUN_ROOT = "/var/lib/eucalyptus-imaging-worker"
SUDO_BIN = "/usr/bin/sudo"

FLOPPY_MOUNT_DIR = RUN_ROOT + "/floppy"
CONFIG_FILE = CONF_ROOT + "/imaging-worker.conf"

# Apply default values in case user does not specify
pidfile = DEFAULT_PIDFILE
pidroot = DEFAULT_PID_ROOT
boto_config = None
cred_provider = None
user_data_store = {}
QUERY_PERIOD_SEC = 30


def get_provider():
    global boto_config
    global cred_provider
    if not cred_provider:
        if boto_config:
            boto.provider.config = boto.Config(boto_config)
        cred_provider = boto.provider.get_default()
    return cred_provider


def set_boto_config(filename):
    if not os.path.isfile(filename):
        raise Exception('could not find boto config {0}'.format(filename))
    global boto_config
    boto_config = filename


# Update pidfile and pidroot variables in global scope.
# This is called if the user has chosen to use a custom
# pidfile location from the command line.
def set_pidfile(filename):
    global pidfile
    global pidroot
    pidfile = filename
    pidroot = os.path.dirname(pidfile)


def read_config_file():
    try:
        f = open(CONFIG_FILE)
        content = f.read()
        lines = content.split('\n')
        for l in lines:
            if len(l.strip()):
                kv = l.split('=')
                if len(kv) == 2:
                    user_data_store[kv[0]] = kv[1]
    except Exception, err:
        raise Exception('Could not read configuration file due to %s' % err)


def get_value(key, optional=False):
    if key in user_data_store:
        return user_data_store[key]
    else:
        read_config_file()
        if key in user_data_store:
            return user_data_store[key]
        else:
            if not optional:
                raise Exception('could not find %s' % key)
            else:
                return None


def get_access_key_id():
    akey = get_provider().get_access_key()
    return akey


def get_secret_access_key():
    skey = get_provider().get_secret_key()
    return skey


def get_security_token():
    token = get_provider().get_security_token()
    return token


def get_imaging_service_url():
    return get_value('imaging_service_url')


def get_compute_service_url():
    return get_value('compute_service_url')


def get_euare_service_url():
    return get_value('euare_service_url')


def get_log_server():
    return get_value('log_server', optional=True)


def get_log_server_port():
    val = get_value('log_server_port', optional=True)
    return int(val) if val is not None else None


def get_ntp_server_url():
    return get_value('ntp_server')


__availability_zone = None


def get_availability_zone():
    global __availability_zone
    if __availability_zone is None:
        resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/placement/availability-zone")
        if resp['status'] != '200' or len(content) <= 0:
            raise Exception('could not query the metadata for availability zone (%s,%s)' % (resp, content))
        __availability_zone = content
    return __availability_zone


__worker_id = None


def get_worker_id():
    global __worker_id
    if __worker_id is None:
        resp, content = httplib2.Http().request("http://169.254.169.254/latest/meta-data/instance-id")
        if resp['status'] != '200' or len(content) <= 0:
            raise Exception('could not query the metadata for instance id (%s,%s)' % (resp, content))
        __worker_id = content
    return __worker_id
