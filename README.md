<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
</head>
<body>

<h1>High-Performance TCP Chat Server</h1>

<p>
A multithreaded TCP-based chat server implemented in C++ to explore
low-level networking, concurrency, and real-world backend system behavior
under load.
</p>

<hr>

<h2>Features</h2>
<ul>
  <li>Supports 1,000+ concurrent TCP clients</li>
  <li>Broadcast and direct (1:1) messaging</li>
  <li>Custom text-based protocol over raw TCP</li>
  <li>Correct handling of TCP stream framing and partial reads</li>
  <li>Thread-safe shared state using mutexes and reader-writer locks</li>
  <li>Deployed on AWS EC2 behind an Nginx TCP (stream) reverse proxy</li>
  <li>Per-IP connection limiting enforced at the Nginx gateway</li>
</ul>

<hr>

<h2>Architecture</h2>
<pre>
Clients
   |
   |  TCP
   v
Nginx (stream proxy, connection limits)
   |
   |  TCP (localhost)
   v
C++ Chat Server (thread-per-client)
</pre>

<hr>

<h2>Stress Testing</h2>
<p>
The server was stress-tested using a Python asyncio-based load generator:
</p>
<ul>
  <li>1,000 concurrent clients</li>
  <li>10 messages per client</li>
  <li>10M+ fan-out messages</li>
  <li>~265K messages/sec throughput (public internet)</li>
  <li>~1.3s average latency, ~3.1s P99 latency under burst load</li>
</ul>

<p>
Testing revealed real-world system behavior such as TCP backpressure,
buffer saturation, and connection resets under sustained load.
</p>

<hr>

<h2>Technologies Used</h2>
<ul>
  <li>C++ (POSIX sockets, pthreads)</li>
  <li>Linux</li>
  <li>TCP/IP networking</li>
  <li>Nginx (stream module)</li>
  <li>AWS EC2</li>
  <li>Python (asyncio for load testing)</li>
</ul>

<hr>

<h2>What This Project Demonstrates</h2>
<ul>
  <li>Understanding of TCP as a byte-stream protocol</li>
  <li>Concurrency control and synchronization</li>
  <li>Reverse proxy configuration for non-HTTP services</li>
  <li>Realistic load testing and performance analysis</li>
  <li>Debugging production-like failures</li>
</ul>

<hr>

<h2>Limitations</h2>
<ul>
  <li>No persistence or message durability</li>
  <li>No authentication or encryption</li>
  <li>Thread-per-client architecture (not event-driven)</li>
</ul>

<p>
This project is intended as a learning exercise in systems and backend
engineering rather than a production-ready chat service.
</p>

<hr>

<h2>Author</h2>
<p>
Built by &lt;Anay Mahajan&gt; as a deep dive into networking and backend systems.
</p>

</body>
</html>
