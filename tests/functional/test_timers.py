# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING.
#
# ***** END LICENSE BLOCK *****
"""
Timer tests, make sure we can add and remove timers and that they fire.
"""
import nose
import os
import sys
sys.path.append('..')
sys.path.append(os.path.join('..', '..'))

import pika
import pika.adapters as adapters

from pika.adapters.tornado_connection import TornadoConnection

HOST = 'localhost'
PORT = 5672


class TestAdapters(object):

    def __init__(self):
        self.connection = None
        self.confirmed = False
        self._timeout = False
        self._timer2 = None

    @nose.tools.timed(2)
    def test_asyncore_connection(self):
        self.connection = self._connect(adapters.AsyncoreConnection)
        self.connection.ioloop.start()
        if not self.confirmed:
            assert False, "Timer tests failed"
        pass

    @nose.tools.timed(2)
    def test_select_connection(self):
        self._set_select_poller('select')
        self.connection = self._connect(adapters.SelectConnection)
        self.connection.ioloop.start()
        if self.connection.ioloop.poller_type != 'SelectPoller':
            assert False
        if not self.confirmed:
            assert False, "Timer tests failed"
        pass

    @nose.tools.timed(2)
    def test_tornado_connection(self):
        self.connection = self._connect(TornadoConnection)
        self.connection.ioloop.start()
        if not self.confirmed:
            assert False, "Timer tests failed"
        pass

    def _connect(self, connection_type):
        if self.connection:
            del self.connection
        self.connected = False
        parameters = pika.ConnectionParameters(HOST, PORT)
        return connection_type(parameters, self._on_connected)

    def _on_connected(self, connection):
        self.connected = self.connection.is_open
        self.connection.add_timeout(0.1, self._on_timer)
        self._timer2 = self.connection.add_timeout(1.5, self._on_fail_timer)

    def _on_timer(self):
        self.confirmed = True
        self.connection.remove_timeout(self._timer2)
        self.connection.add_on_close_callback(self._on_closed)
        self.connection.close()

    def _on_fail_timer(self):
        assert False, "_on_fail_timer was fired and not removed"

    def _on_closed(self, frame):
        self.connection.ioloop.stop()

    def _set_select_poller(self, type):
        adapters.select_connection.SELECT_TYPE = type

if __name__ == "__main__":
    nose.runmodule()
