# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and
# limitations under the License.
#
# The Original Code is Pika.
#
# The Initial Developers of the Original Code are LShift Ltd, Cohesive
# Financial Technologies LLC, and Rabbit Technologies Ltd.  Portions
# created before 22-Nov-2008 00:00:00 GMT by LShift Ltd, Cohesive
# Financial Technologies LLC, or Rabbit Technologies Ltd are Copyright
# (C) 2007-2008 LShift Ltd, Cohesive Financial Technologies LLC, and
# Rabbit Technologies Ltd.
#
# Portions created by LShift Ltd are Copyright (C) 2007-2009 LShift
# Ltd. Portions created by Cohesive Financial Technologies LLC are
# Copyright (C) 2007-2009 Cohesive Financial Technologies
# LLC. Portions created by Rabbit Technologies Ltd are Copyright (C)
# 2007-2009 Rabbit Technologies Ltd.
#
# Portions created by Tony Garnock-Jones are Copyright (C) 2009-2010
# LShift Ltd and Tony Garnock-Jones.
#
# All Rights Reserved.
#
# Contributor(s): ______________________________________.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public License Version 2 or later (the "GPL"), in
# which case the provisions of the GPL are applicable instead of those
# above. If you wish to allow use of your version of this file only
# under the terms of the GPL, and not to allow others to use your
# version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the
# notice and other provisions required by the GPL. If you do not
# delete the provisions above, a recipient may use your version of
# this file under the terms of any one of the MPL or the GPL.
#
# ***** END LICENSE BLOCK *****

# Async pika testing support

import sys
sys.path.append('..')

import os
import pika
import time

timeout_id = None


def test_queue_name(keyword):
    return 'test-%s-%i' % (keyword, os.getpid())


# These methods are scoped to the AsyncPattern class
def timeout(method):
    def _timeout(self, *args, **kwargs):
        global timeout_id
        timeout_id = self.connection.add_timeout(2, self._on_timeout)
        return method(self, *args, **kwargs)
    return _timeout


def timeout_cancel(method):
    def _timeout(self, *args, **kwargs):
        global timeout_id
        self.connection.remove_timeout(timeout_id)
        del(timeout_id)
        return method(self, *args, **kwargs)
    return _timeout


class AsyncPattern(object):

    def __init__(self):
        self.connection = None
        self.channel = None
        self._queue = self._queue_name()
        self._timeout = False

    def _queue_name(self):
        return 'test-%s-%i' % (self.__class__.__name__, os.getpid())

    def _connect(self, connection_type, host, port):
        parameters = pika.ConnectionParameters(host, port)
        return connection_type(parameters, self._on_connected)

    def _on_connected(self, connection):
        self.connection.channel(self._on_channel)

    def _on_channel(self, channel):
        assert False, "_on_channel no _extended"

    def _queue_declare(self):
        self.channel.queue_declare(queue=self._queue,
                                   durable=False,
                                   exclusive=False,
                                   auto_delete=True,
                                   callback=self._on_queue_declared)

    def _on_queue_declared(self, frame):
        assert False, "_on_queue_declared not extended"

    def _send_message(self, exchange='', mandatory=False, immediate=False):

        message = 'test-message-%s: %.8f' % (self.__class__.__name__,
                                             time.time())
        self.channel.basic_publish(exchange=exchange,
                                   routing_key=self._queue,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       content_type="text/plain",
                                       delivery_mode=1),
                                   mandatory=mandatory,
                                   immediate=immediate)
        return message

    @property
    def _is_connected(connection):
        return self.connection.is_open

    def _on_timeout(self):
        self._timeout = True
        self.connection.add_on_close_callback(self._on_closed)
        self.connection.close()

    def _on_closed(self, frame):
        self.connection.ioloop.stop()
