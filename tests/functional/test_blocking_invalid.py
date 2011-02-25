# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING.
#
# ***** END LICENSE BLOCK *****
"""
Send a message to a non-existent queue with the mandatory flag and confirm
that it is returned via Basic.Return
"""
import nose
import os
import sys
import time
sys.path.append('..')
sys.path.append(os.path.join('..', '..'))

import pika
import pika.exceptions
from pika.adapters import BlockingConnection
import support.tools

HOST = 'localhost'
PORT = 5672


def test_blocking_send_get():

    parameters = pika.ConnectionParameters(host=HOST, port=PORT)
    connection = BlockingConnection(parameters)

    # Open the channel
    channel = connection.channel()

    # Declare the queue
    queue_name = support.tools.test_queue_name('blocking_send_get')
    channel.queue_declare(queue=queue_name,
                          durable=False,
                          exclusive=True,
                          auto_delete=True)

    message = 'test_blocking_send:%.4f' % time.time()
    try:
        channel.basic_publish(exchange='undeclared-exchange',
                              routing_key=queue_name,
                              body=message,
                              properties=pika.BasicProperties(
                                content_type="text/plain",
                                delivery_mode=1))
    except pika.exceptions.AMQPChannelError, error:
        if error[0] != 404:
            assert False, "Did not receive a Channel.Close"
    connection.close()

if __name__ == "__main__":
    nose.runmodule()
