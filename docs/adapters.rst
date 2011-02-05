Connection Adapters
===================
Pika provides multiple adapters to connect to RabbitMQ allowing for different ways of providing socket communication depending on what is appropriate for your application.

- :ref:`SelectConnection`: A native event based connection adapter that implements select, kqueue, poll and epoll.
- :ref:`AsyncoreConnection`: Legacy adapter kept for convenience of previous Pika users.
- :ref:`TornadoConnection`: Connection adapter for use with the Tornado IO Loop.
- :ref:`BlockingConnection`: Enables blocking, synchronous operation on top of library for simple uses.

.. _intro_to_backpressure:

TCP Backpressure
----------------

As of RabbitMQ 2.0.0, client side Channel.Flow has been removed. Instead, the RabbitMQ broker uses TCP Backpressure to slow your client if it is
delivering messages too fast. Pika attempts to help you handle this situation by providing a mechanism by which you may be notified if Pika has noticed
too many frames have yet to be delivered. By registering a function with the *add_backpressure_callback* function of any connection adapter, your function
will be called when Pika sees that a backlog of 10 times the average frame size you have been sending has been exceeded. You may tweak this value by
calling the set_backpressure_multiplier method passing any integer value.

.. _intro_to_ioloop:

IO and Event Looping
--------------------

Due to the need to check for and send content on a consistent basis, Pika now implements or extends IOLoops in each of its asynchronous connection adapters. These IOLoops are blocking methods which loop and listen for events. Each asynchronous adapters follows the same standard for invoking the IOLoop. The IOLoop is
created when the connection adapter is created. To start it simply call the connection.ioloop.start() method.

If you are using an external IOLoop such as Tornado's IOLoop, you may invoke that as you normally would and then add the adapter to it.

Example::

    # Create our connection object
    connection = SelectConnection()

    try:
        # Loop so we can communicate with RabbitMQ
        connection.ioloop.start()
    except KeyboardInterrupt:
        # Gracefully close the connection
        connection.close()
        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()


.. _intro_to_cps:

Continuation-Passing Style
--------------------------

Interfacing with Pika asynchronously is done by passing in callback methods you would like to have invoked when a certain event has completed. For example, if you are going to declare a queue, you pass in a method that will be called when the RabbitMQ server returns a "Queue.DeclareOk" response.

In our example below we use the following four easy steps:

#. We start by creating our connection object, then starting our event loop.
#. When we are connected, the *on_connected* method is called. In that method we create a channel.
#. When the channel is created, the *on_channel_open* method is called. In that method we declare a queue.
#. When the queue is declared successfully, *on_queue_declared* is called. In that method we call channel.basic_consume telling it to call the handle_delivery for each message RabbitMQ delivers to us.

.. _cps_example:

Example::

    from pika.adapters import SelectConnection

    # Create a global channel variable to hold our channel object in
    channel = None

    # Step #2
    def on_connected(connection):
        """Called when we are fully connected to RabbitMQ"""
        # Open a channel
        connection.channel(on_channel_open)

    # Step #3
    def on_channel_open(new_channel):
        """Called when our channel has opened"""
        global channel
        channel = new_channel
        channel.queue_declare(queue="test", durable=True, exclusive=False, auto_delete=False, callback=on_queue_declared)

    # Step #4
    def on_queue_declared(frame):
        """Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
        channel.basic_consume(handle_delivery, queue='test')

    def handle_delivery(channel, method, header, body):
        """Called when we receive a message from RabbitMQ"""
        print body

    # Step #1: Connect to RabbitMQ
    connection = SelectConnection(parameters, on_connected)

    try:
        # Loop so we can communicate with RabbitMQ
        connection.ioloop.start()
    except KeyboardInterrupt:
        # Gracefully close the connection
        connection.close()
        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()

Available Adapters
------------------

.. _selectconnection:

SelectConnection
^^^^^^^^^^^^^^^^

.. NOTE::
    SelectConnection is the recommended method for using Pika under most circumstances. It supports multiple event notification methods including select, epoll, kqueue and poll.

By default SelectConnection will attempt to use the most appropriate event
notification method for your system. In order to override the default behavior
you may set the poller type by assigning a string value to the
select_connection modules POLLER_TYPE attribute prior to creating the
SelectConnection object instance. Valid values are: kqueue, poll, epoll, select

Poller Type Override Example::

  import select_connection
  select_connection.POLLER_TYPE = 'epoll'
  connection = select_connection.SelectConnection()

See the :ref:`Continuation-Passing Style example <cps_example>` for an example of using SelectConnection.

.. automodule:: adapters.select_connection
.. autoclass:: SelectConnection
   :member-order: bysource
   :inherited-members:

.. _asyncoreconnection:

AsyncoreConnection
^^^^^^^^^^^^^^^^^^
.. NOTE::
    Use SelectConnection, the method signatures are the same.

The AsyncoreConnection class is provided for legacy support and quicker porting from applications that used Pika version 0.5.2 and prior.

.. automodule:: adapters.asyncore_connection
.. autoclass:: AsyncoreConnection
   :members:
   :inherited-members:
   :member-order: bysource

.. _tornadoconnection:

TornadoConnection
^^^^^^^^^^^^^^^^^

Tornado is an open source version of the scalable, non-blocking web server and tools that power FriendFeed. For more information on tornado, visit http://tornadoweb.org

Since the Tornado IOLoop blocks once it is started, it is suggested that you use a timer to add Pika to your tornado.Application instance after the HTTPServer has started.

The following is a simple, non-working example on how to add Pika to the Tornado IOLoop without blocking other applications from doing so. To see a fully workng example,
see the Tornado Demo application in the examples.

Example::

    from pika.adapters.tornado_connection import TornadoConnection()

    class PikaClient(object):
        def connect(self):
            self.connection = TornadoConnection(on_connected_callback=self.on_connected)

    # Create our Tornado Application
    application = tornado.web.Application([
        (r"/", ExampleHandler)
    ], **settings)

    # Create our Pika Client
    application.pika = PikaClient()

    # Start the HTTPServer
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8080)

    # Get a handle to the instance of IOLoop
    ioloop = tornado.ioloop.IOLoop.instance()

    # Add our Pika connect to the IOLoop since we loop on ioloop.start
    ioloop.add_timeout(500, application.pika.connect)

    # Start the IOLoop
    ioloop.start()

.. automodule:: adapters.tornado_connection
.. autoclass:: TornadoConnection
   :members:
   :inherited-members:
   :member-order: bysource

.. _blockingconnection:

BlockingConnection
^^^^^^^^^^^^^^^^^^
.. Warning::
   BlockingConnection is provided for legacy and learning purposes only and it is not recommended that you use it for a production application.

The BlockingConnection creates a layer on top of Pika's asynchronous core providng methods that will block until their expected response has returned.
Due to the asynchronous nature of the Basic.Deliver and Basic.Return calls from RabbitMQ to your application, you are still required to implement
continuation-passing style asynchronous methods if you'd like to receive messages from RabbitMQ using basic_consume or if you want to be notified of
a delivery failure when using basic_publish.

Basic.Get is a blocking call which will either return the Method Frame, Header Frame and Body of a message, or it will return a Basic.GetEmpty frame as the Method Frame.

Example::

    # Open a connection to RabbitMQ on localhost using all default parameters
    connection = BlockingConnection()

    # Open the channel
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue="test", durable=True, exclusive=False, auto_delete=False)

    channel.basic_publish(exchange='', routing_key="test", body="Hello World!",
                          properties=pika.BasicProperties(content_type="text/plain", delivery_mode=1))

.. automodule:: adapters.blocking_connection
.. autoclass:: BlockingConnection
   :members:
   :inherited-members:
   :member-order: bysource