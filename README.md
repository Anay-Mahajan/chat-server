<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
</head>
<body>

<h1>Multithreaded TCP Chat Server (C++)</h1>

<p>
A <strong>multithreaded TCP chat server</strong> implemented in <strong>C++</strong> using
<strong>POSIX sockets</strong>, designed to handle <strong>1,000+ concurrent clients</strong>
with correct message framing, thread-safe routing, and backpressure-aware behavior.
</p>

<p>
This project focuses on <strong>networking fundamentals, concurrency, and systems-level correctness</strong>,
rather than UI or product features.
</p>

<hr>

<h2>Features</h2>
<ul>
  <li>Persistent TCP connections (thread-per-client model)</li>
  <li>Custom newline-delimited text protocol</li>
  <li>User registration, broadcast, and direct messaging</li>
  <li>Thread-safe connection and message management</li>
  <li>Correct handling of TCP stream semantics (partial reads, coalesced packets)</li>
  <li>Graceful handling of disconnects and slow clients</li>
</ul>

<hr>

<h2>Architecture</h2>

<pre>
Clients (CLI)
    |
TCP Connections
    |
Multithreaded C++ Server
    |
Thread-safe Message Routing
</pre>

<ul>
  <li>Each client connection is handled by a dedicated thread</li>
  <li>Shared state protected using <code>std::shared_mutex</code></li>
  <li>No blocking network I/O while holding exclusive locks</li>
</ul>

<hr>

<h2>Protocol</h2>

<p>All messages <strong>must end with <code>\n</code></strong>.</p>

<pre>
@advertize &lt;username&gt;\n
@all &lt;message&gt;\n
@&lt;username&gt; &lt;message&gt;\n
</pre>

<hr>

<h2>Performance (Representative)</h2>
<ul>
  <li>Tested with ~1,000 concurrent clients</li>
  <li>Sustained throughput: <strong>~600K–700K messages/sec (fan-out)</strong></li>
  <li>Average latency: <strong>&lt; 0.5 second</strong></li>
  <li>P99 latency: <strong>~1.1 seconds</strong></li>
</ul>

<p><em>Results vary based on hardware and OS settings.</em></p>

<hr>

<h2>Build &amp; Run (CMake)</h2>

<h4>Build</h4>
<pre>
mkdir build
cd build
cmake ..
make
</pre>

<h4>Run Server</h4>
<pre>
cd build
./server
</pre>

<h4>Run Client</h4>
<pre>
cd build
./client
</pre>

<hr>

<h2>Limitations</h2>
<ul>
  <li>Thread-per-client model limits scalability</li>
  <li>Blocking I/O under heavy fan-out</li>
  <li>In-memory only (no persistence)</li>
  <li>No authentication or TLS</li>
</ul>

<p>
These limitations are <strong>intentional</strong> to highlight architectural tradeoffs.
</p>

<hr>

<h2>Key Learnings</h2>
<ul>
  <li>TCP is a byte stream — explicit message framing is required</li>
  <li>Backpressure is expected and must be handled</li>
  <li>Concurrency bugs appear under load, not at small scale</li>
  <li>Measuring performance is as important as correctness</li>
</ul>

<hr>

</body>
</html>
