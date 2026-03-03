<!-- fetch_source.py metadata
url: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
fetched: 2026-03-03T04:21:06Z
http_status: 200
-->
# Fetched source: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
_Fetched: 2026-03-03T04:21:06Z | HTTP 200_

---

<!DOCTYPE html>
<html class="writer-html5" lang="en">
<head>
  <meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />

  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OpenTelemetry FastAPI Instrumentation &mdash; OpenTelemetry Python Contrib  documentation</title>
      <link rel="stylesheet" type="text/css" href="../../_static/pygments.css?v=b86133f3" />
      <link rel="stylesheet" type="text/css" href="../../_static/css/theme.css?v=19f00094" />

  
  <!--[if lt IE 9]>
    <script src="../../_static/js/html5shiv.min.js"></script>
  <![endif]-->
  
        <script src="../../_static/jquery.js?v=5d32c60e"></script>
        <script src="../../_static/_sphinx_javascript_frameworks_compat.js?v=2cd50e6c"></script>
        <script data-url_root="../../" id="documentation_options" src="../../_static/documentation_options.js?v=b3ba4146"></script>
        <script src="../../_static/doctools.js?v=888ff710"></script>
        <script src="../../_static/sphinx_highlight.js?v=4825356b"></script>
    <script src="../../_static/js/theme.js"></script>
    <link rel="index" title="Index" href="../../genindex.html" />
    <link rel="search" title="Search" href="../../search.html" />
    <link rel="next" title="OpenTelemetry Flask Instrumentation" href="../flask/flask.html" />
    <link rel="prev" title="OpenTelemetry Falcon Instrumentation" href="../falcon/falcon.html" /> 
<script async type="text/javascript" src="/_/static/javascript/readthedocs-addons.js"></script><meta name="readthedocs-project-slug" content="opentelemetry-python-contrib" /><meta name="readthedocs-version-slug" content="latest" /><meta name="readthedocs-resolver-filename" content="/instrumentation/fastapi/fastapi.html" /><meta name="readthedocs-http-status" content="200" /></head>

<body class="wy-body-for-nav"> 
  <div class="wy-grid-for-nav">
    <nav data-toggle="wy-nav-shift" class="wy-nav-side">
      <div class="wy-side-scroll">
        <div class="wy-side-nav-search" >

          
          
          <a href="../../index.html" class="icon icon-home">
            OpenTelemetry Python Contrib
          </a>
<div role="search">
  <form id="rtd-search-form" class="wy-form" action="../../search.html" method="get">
    <input type="text" name="q" placeholder="Search docs" aria-label="Search docs" />
    <input type="hidden" name="check_keywords" value="yes" />
    <input type="hidden" name="area" value="default" />
  </form>
</div>
        </div><div class="wy-menu wy-menu-vertical" data-spy="affix" role="navigation" aria-label="Navigation menu">
              <p class="caption" role="heading"><span class="caption-text">OpenTelemetry Instrumentations</span></p>
<ul class="current">
<li class="toctree-l1"><a class="reference internal" href="../aio_pika/aio_pika.html">OpenTelemetry aio pika Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../aiohttp_client/aiohttp_client.html">OpenTelemetry aiohttp client Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../aiohttp_server/aiohttp_server.html">OpenTelemetry aiohttp server Integration</a></li>
<li class="toctree-l1"><a class="reference internal" href="../aiokafka/aiokafka.html">OpenTelemetry aiokafka instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../aiopg/aiopg.html">OpenTelemetry aiopg Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../asgi/asgi.html">OpenTelemetry ASGI Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../asyncclick/asyncclick.html">OpenTelemetry asyncclick Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../asyncio/asyncio.html">OpenTelemetry asyncio Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../asyncpg/asyncpg.html">OpenTelemetry asyncpg Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../aws_lambda/aws_lambda.html">OpenTelemetry AWS lambda Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../base/instrumentation.html">OpenTelemetry Python Instrumentor</a></li>
<li class="toctree-l1"><a class="reference internal" href="../base/instrumentor.html">opentelemetry.instrumentation.instrumentor package</a></li>
<li class="toctree-l1"><a class="reference internal" href="../boto/boto.html">OpenTelemetry Boto Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../boto3sqs/boto3sqs.html">OpenTelemetry Boto3 SQS Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../botocore/botocore.html">OpenTelemetry Botocore Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../cassandra/cassandra.html">OpenTelemetry Cassandra Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../celery/celery.html">OpenTelemetry Celery Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../click/click.html">OpenTelemetry click Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../confluent_kafka/confluent_kafka.html">OpenTelemetry confluent-kafka Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../dbapi/dbapi.html">OpenTelemetry Database API Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../django/django.html">OpenTelemetry Django Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../elasticsearch/elasticsearch.html">OpenTelemetry elasticsearch Integration</a></li>
<li class="toctree-l1"><a class="reference internal" href="../falcon/falcon.html">OpenTelemetry Falcon Instrumentation</a></li>
<li class="toctree-l1 current"><a class="current reference internal" href="#">OpenTelemetry FastAPI Instrumentation</a><ul>
<li class="toctree-l2"><a class="reference internal" href="#installation">Installation</a></li>
<li class="toctree-l2"><a class="reference internal" href="#references">References</a></li>
<li class="toctree-l2"><a class="reference internal" href="#module-opentelemetry.instrumentation.fastapi">API</a><ul>
<li class="toctree-l3"><a class="reference internal" href="#usage">Usage</a></li>
<li class="toctree-l3"><a class="reference internal" href="#configuration">Configuration</a><ul>
<li class="toctree-l4"><a class="reference internal" href="#exclude-lists">Exclude lists</a></li>
<li class="toctree-l4"><a class="reference internal" href="#request-response-hooks">Request/Response hooks</a></li>
<li class="toctree-l4"><a class="reference internal" href="#capture-http-request-and-response-headers">Capture HTTP request and response headers</a></li>
<li class="toctree-l4"><a class="reference internal" href="#request-headers">Request headers</a></li>
<li class="toctree-l4"><a class="reference internal" href="#response-headers">Response headers</a></li>
<li class="toctree-l4"><a class="reference internal" href="#sanitizing-headers">Sanitizing headers</a></li>
</ul>
</li>
<li class="toctree-l3"><a class="reference internal" href="#id1">API</a></li>
<li class="toctree-l3"><a class="reference internal" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor"><code class="docutils literal notranslate"><span class="pre">FastAPIInstrumentor</span></code></a><ul>
<li class="toctree-l4"><a class="reference internal" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app"><code class="docutils literal notranslate"><span class="pre">FastAPIInstrumentor.instrument_app()</span></code></a></li>
<li class="toctree-l4"><a class="reference internal" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.uninstrument_app"><code class="docutils literal notranslate"><span class="pre">FastAPIInstrumentor.uninstrument_app()</span></code></a></li>
<li class="toctree-l4"><a class="reference internal" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrumentation_dependencies"><code class="docutils literal notranslate"><span class="pre">FastAPIInstrumentor.instrumentation_dependencies()</span></code></a></li>
</ul>
</li>
</ul>
</li>
</ul>
</li>
<li class="toctree-l1"><a class="reference internal" href="../flask/flask.html">OpenTelemetry Flask Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../grpc/grpc.html">OpenTelemetry gRPC Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../httpx/httpx.html">OpenTelemetry HTTPX Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../jinja2/jinja2.html">OpenTelemetry Jinja2 Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../kafka_python/kafka_python.html">OpenTelemetry kafka-python integration</a></li>
<li class="toctree-l1"><a class="reference internal" href="../logging/logging.html">OpenTelemetry Logging Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../mysql/mysql.html">OpenTelemetry MySQL Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../mysqlclient/mysqlclient.html">OpenTelemetry mysqlclient Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pika/pika.html">OpenTelemetry Pika Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../psycopg/psycopg.html">OpenTelemetry Psycopg Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../psycopg2/psycopg2.html">OpenTelemetry Psycopg2 Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pymemcache/pymemcache.html">OpenTelemetry pymemcache Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pymongo/pymongo.html">OpenTelemetry pymongo Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pymssql/pymssql.html">OpenTelemetry pymssql Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pymysql/pymysql.html">OpenTelemetry PyMySQL Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../pyramid/pyramid.html">OpenTelemetry Pyramid Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../redis/redis.html">OpenTelemetry Redis Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../remoulade/remoulade.html">OpenTelemetry Remoulade Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../requests/requests.html">OpenTelemetry requests Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../sqlalchemy/sqlalchemy.html">OpenTelemetry SQLAlchemy Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../sqlite3/sqlite3.html">OpenTelemetry SQLite3 Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../starlette/starlette.html">OpenTelemetry Starlette Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../system_metrics/system_metrics.html">OpenTelemetry system metrics Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../threading/threading.html">OpenTelemetry Threading Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../tornado/tornado.html">OpenTelemetry Tornado Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../tortoiseorm/tortoiseorm.html">OpenTelemetry Tortoise ORM Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../urllib/urllib3.html">OpenTelemetry urllib Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../urllib3/urllib3.html">OpenTelemetry urllib3 Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../wsgi/wsgi.html">OpenTelemetry WSGI Instrumentation</a></li>
</ul>
<p class="caption" role="heading"><span class="caption-text">OpenTelemetry Generative AI Instrumentations</span></p>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../../instrumentation-genai/openai.html">OpenTelemetry Python - OpenAI Instrumentation</a></li>
<li class="toctree-l1"><a class="reference internal" href="../../instrumentation-genai/util.html">OpenTelemetry Python - GenAI Util</a></li>
</ul>
<p class="caption" role="heading"><span class="caption-text">OpenTelemetry Propagators</span></p>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../../propagator/aws/aws.html">OpenTelemetry Python - AWS X-Ray Propagator</a></li>
</ul>
<p class="caption" role="heading"><span class="caption-text">OpenTelemetry Performance</span></p>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../../performance/benchmarks.html">Performance Tests - Benchmarks</a></li>
</ul>
<p class="caption" role="heading"><span class="caption-text">OpenTelemetry SDK Extensions</span></p>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../../sdk-extension/aws/aws.html">OpenTelemetry Python - AWS SDK Extension</a></li>
</ul>
<p class="caption" role="heading"><span class="caption-text">OpenTelemetry Resource Detectors</span></p>
<ul>
<li class="toctree-l1"><a class="reference internal" href="../../resource/container/container.html">OpenTelemetry Python - Resource Detector for Containers</a></li>
</ul>

        </div>
      </div>
    </nav>

    <section data-toggle="wy-nav-shift" class="wy-nav-content-wrap"><nav class="wy-nav-top" aria-label="Mobile navigation menu" >
          <i data-toggle="wy-nav-top" class="fa fa-bars"></i>
          <a href="../../index.html">OpenTelemetry Python Contrib</a>
      </nav>

      <div class="wy-nav-content">
        <div class="rst-content">
          <div role="navigation" aria-label="Page navigation">
  <ul class="wy-breadcrumbs">
      <li><a href="../../index.html" class="icon icon-home" aria-label="Home"></a></li>
      <li class="breadcrumb-item active">OpenTelemetry FastAPI Instrumentation</li>
      <li class="wy-breadcrumbs-aside">
            <a href="../../_sources/instrumentation/fastapi/fastapi.rst.txt" rel="nofollow"> View page source</a>
      </li>
  </ul>
  <hr/>
</div>
          <div role="main" class="document" itemscope="itemscope" itemtype="http://schema.org/Article">
           <div itemprop="articleBody">
             
  <section id="opentelemetry-fastapi-instrumentation">
<h1>OpenTelemetry FastAPI Instrumentation<a class="headerlink" href="#opentelemetry-fastapi-instrumentation" title="Permalink to this heading"></a></h1>
<p><a class="reference external" href="https://pypi.org/project/opentelemetry-instrumentation-fastapi/"><img alt="pypi" src="https://badge.fury.io/py/opentelemetry-instrumentation-fastapi.svg" /></a></p>
<p>This library provides automatic and manual instrumentation of FastAPI web frameworks,
instrumenting http requests served by applications utilizing the framework.</p>
<p>auto-instrumentation using the opentelemetry-instrumentation package is also supported.</p>
<section id="installation">
<h2>Installation<a class="headerlink" href="#installation" title="Permalink to this heading"></a></h2>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">pip</span> <span class="n">install</span> <span class="n">opentelemetry</span><span class="o">-</span><span class="n">instrumentation</span><span class="o">-</span><span class="n">fastapi</span>
</pre></div>
</div>
</section>
<section id="references">
<h2>References<a class="headerlink" href="#references" title="Permalink to this heading"></a></h2>
<ul class="simple">
<li><p><a class="reference external" href="https://opentelemetry.io/">OpenTelemetry Project</a></p></li>
<li><p><a class="reference external" href="https://github.com/open-telemetry/opentelemetry-python/tree/main/docs/examples">OpenTelemetry Python Examples</a></p></li>
</ul>
</section>
<section id="module-opentelemetry.instrumentation.fastapi">
<span id="api"></span><h2>API<a class="headerlink" href="#module-opentelemetry.instrumentation.fastapi" title="Permalink to this heading"></a></h2>
<section id="usage">
<h3>Usage<a class="headerlink" href="#usage" title="Permalink to this heading"></a></h3>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="kn">import</span><span class="w"> </span><span class="nn">fastapi</span>
<span class="kn">from</span><span class="w"> </span><span class="nn">opentelemetry.instrumentation.fastapi</span><span class="w"> </span><span class="kn">import</span> <span class="n">FastAPIInstrumentor</span>

<span class="n">app</span> <span class="o">=</span> <span class="n">fastapi</span><span class="o">.</span><span class="n">FastAPI</span><span class="p">()</span>

<span class="nd">@app</span><span class="o">.</span><span class="n">get</span><span class="p">(</span><span class="s2">&quot;/foobar&quot;</span><span class="p">)</span>
<span class="k">async</span> <span class="k">def</span><span class="w"> </span><span class="nf">foobar</span><span class="p">():</span>
    <span class="k">return</span> <span class="p">{</span><span class="s2">&quot;message&quot;</span><span class="p">:</span> <span class="s2">&quot;hello world&quot;</span><span class="p">}</span>

<span class="n">FastAPIInstrumentor</span><span class="o">.</span><span class="n">instrument_app</span><span class="p">(</span><span class="n">app</span><span class="p">)</span>
</pre></div>
</div>
</section>
<section id="configuration">
<h3>Configuration<a class="headerlink" href="#configuration" title="Permalink to this heading"></a></h3>
<section id="exclude-lists">
<h4>Exclude lists<a class="headerlink" href="#exclude-lists" title="Permalink to this heading"></a></h4>
<p>To exclude certain URLs from tracking, set the environment variable <code class="docutils literal notranslate"><span class="pre">OTEL_PYTHON_FASTAPI_EXCLUDED_URLS</span></code>
(or <code class="docutils literal notranslate"><span class="pre">OTEL_PYTHON_EXCLUDED_URLS</span></code> to cover all instrumentations) to a string of comma delimited regexes that match the
URLs.</p>
<p>For example,</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_PYTHON_FASTAPI_EXCLUDED_URLS</span><span class="o">=</span><span class="s2">&quot;client/.*/info,healthcheck&quot;</span>
</pre></div>
</div>
<p>will exclude requests such as <code class="docutils literal notranslate"><span class="pre">https://site/client/123/info</span></code> and <code class="docutils literal notranslate"><span class="pre">https://site/xyz/healthcheck</span></code>.</p>
<p>You can also pass comma delimited regexes directly to the <code class="docutils literal notranslate"><span class="pre">instrument_app</span></code> method:</p>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="n">FastAPIInstrumentor</span><span class="o">.</span><span class="n">instrument_app</span><span class="p">(</span><span class="n">app</span><span class="p">,</span> <span class="n">excluded_urls</span><span class="o">=</span><span class="s2">&quot;client/.*/info,healthcheck&quot;</span><span class="p">)</span>
</pre></div>
</div>
</section>
<section id="request-response-hooks">
<h4>Request/Response hooks<a class="headerlink" href="#request-response-hooks" title="Permalink to this heading"></a></h4>
<p>This instrumentation supports request and response hooks. These are functions that get called
right after a span is created for a request and right before the span is finished for the response.</p>
<ul class="simple">
<li><p>The server request hook is passed a server span and ASGI scope object for every incoming request.</p></li>
<li><p>The client request hook is called with the internal span, and ASGI scope and event when the method <code class="docutils literal notranslate"><span class="pre">receive</span></code> is called.</p></li>
<li><p>The client response hook is called with the internal span, and ASGI scope and event when the method <code class="docutils literal notranslate"><span class="pre">send</span></code> is called.</p></li>
</ul>
<div class="highlight-python notranslate"><div class="highlight"><pre><span></span><span class="kn">from</span><span class="w"> </span><span class="nn">opentelemetry.instrumentation.fastapi</span><span class="w"> </span><span class="kn">import</span> <span class="n">FastAPIInstrumentor</span>
<span class="kn">from</span><span class="w"> </span><span class="nn">opentelemetry.trace</span><span class="w"> </span><span class="kn">import</span> <span class="n">Span</span>
<span class="kn">from</span><span class="w"> </span><span class="nn">typing</span><span class="w"> </span><span class="kn">import</span> <span class="n">Any</span>

<span class="k">def</span><span class="w"> </span><span class="nf">server_request_hook</span><span class="p">(</span><span class="n">span</span><span class="p">:</span> <span class="n">Span</span><span class="p">,</span> <span class="n">scope</span><span class="p">:</span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">]):</span>
    <span class="k">if</span> <span class="n">span</span> <span class="ow">and</span> <span class="n">span</span><span class="o">.</span><span class="n">is_recording</span><span class="p">():</span>
        <span class="n">span</span><span class="o">.</span><span class="n">set_attribute</span><span class="p">(</span><span class="s2">&quot;custom_user_attribute_from_request_hook&quot;</span><span class="p">,</span> <span class="s2">&quot;some-value&quot;</span><span class="p">)</span>

<span class="k">def</span><span class="w"> </span><span class="nf">client_request_hook</span><span class="p">(</span><span class="n">span</span><span class="p">:</span> <span class="n">Span</span><span class="p">,</span> <span class="n">scope</span><span class="p">:</span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">],</span> <span class="n">message</span><span class="p">:</span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">]):</span>
    <span class="k">if</span> <span class="n">span</span> <span class="ow">and</span> <span class="n">span</span><span class="o">.</span><span class="n">is_recording</span><span class="p">():</span>
        <span class="n">span</span><span class="o">.</span><span class="n">set_attribute</span><span class="p">(</span><span class="s2">&quot;custom_user_attribute_from_client_request_hook&quot;</span><span class="p">,</span> <span class="s2">&quot;some-value&quot;</span><span class="p">)</span>

<span class="k">def</span><span class="w"> </span><span class="nf">client_response_hook</span><span class="p">(</span><span class="n">span</span><span class="p">:</span> <span class="n">Span</span><span class="p">,</span> <span class="n">scope</span><span class="p">:</span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">],</span> <span class="n">message</span><span class="p">:</span> <span class="nb">dict</span><span class="p">[</span><span class="nb">str</span><span class="p">,</span> <span class="n">Any</span><span class="p">]):</span>
    <span class="k">if</span> <span class="n">span</span> <span class="ow">and</span> <span class="n">span</span><span class="o">.</span><span class="n">is_recording</span><span class="p">():</span>
        <span class="n">span</span><span class="o">.</span><span class="n">set_attribute</span><span class="p">(</span><span class="s2">&quot;custom_user_attribute_from_response_hook&quot;</span><span class="p">,</span> <span class="s2">&quot;some-value&quot;</span><span class="p">)</span>

<span class="n">FastAPIInstrumentor</span><span class="p">()</span><span class="o">.</span><span class="n">instrument</span><span class="p">(</span><span class="n">server_request_hook</span><span class="o">=</span><span class="n">server_request_hook</span><span class="p">,</span> <span class="n">client_request_hook</span><span class="o">=</span><span class="n">client_request_hook</span><span class="p">,</span> <span class="n">client_response_hook</span><span class="o">=</span><span class="n">client_response_hook</span><span class="p">)</span>
</pre></div>
</div>
</section>
<section id="capture-http-request-and-response-headers">
<h4>Capture HTTP request and response headers<a class="headerlink" href="#capture-http-request-and-response-headers" title="Permalink to this heading"></a></h4>
<p>You can configure the agent to capture specified HTTP headers as span attributes, according to the
<a class="reference external" href="https://github.com/open-telemetry/semantic-conventions/blob/main/docs/http/http-spans.md#http-server-span">semantic conventions</a>.</p>
</section>
<section id="request-headers">
<h4>Request headers<a class="headerlink" href="#request-headers" title="Permalink to this heading"></a></h4>
<p>To capture HTTP request headers as span attributes, set the environment variable
<code class="docutils literal notranslate"><span class="pre">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST</span></code> to a comma delimited list of HTTP header names,
or pass the <code class="docutils literal notranslate"><span class="pre">http_capture_headers_server_request</span></code> keyword argument to the <code class="docutils literal notranslate"><span class="pre">instrument_app</span></code> method.</p>
<p>For example using the environment variable,</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST</span><span class="o">=</span><span class="s2">&quot;content-type,custom_request_header&quot;</span>
</pre></div>
</div>
<p>will extract <code class="docutils literal notranslate"><span class="pre">content-type</span></code> and <code class="docutils literal notranslate"><span class="pre">custom_request_header</span></code> from the request headers and add them as span attributes.</p>
<p>Request header names in FastAPI are case-insensitive. So, giving the header name as <code class="docutils literal notranslate"><span class="pre">CUStom-Header</span></code> in the environment
variable will capture the header named <code class="docutils literal notranslate"><span class="pre">custom-header</span></code>.</p>
<p>Regular expressions may also be used to match multiple headers that correspond to the given pattern.  For example:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST</span><span class="o">=</span><span class="s2">&quot;Accept.*,X-.*&quot;</span>
</pre></div>
</div>
<p>Would match all request headers that start with <code class="docutils literal notranslate"><span class="pre">Accept</span></code> and <code class="docutils literal notranslate"><span class="pre">X-</span></code>.</p>
<p>To capture all request headers, set <code class="docutils literal notranslate"><span class="pre">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST</span></code> to <code class="docutils literal notranslate"><span class="pre">&quot;.*&quot;</span></code>.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST</span><span class="o">=</span><span class="s2">&quot;.*&quot;</span>
</pre></div>
</div>
<p>The name of the added span attribute will follow the format <code class="docutils literal notranslate"><span class="pre">http.request.header.&lt;header_name&gt;</span></code> where <code class="docutils literal notranslate"><span class="pre">&lt;header_name&gt;</span></code>
is the normalized HTTP header name (lowercase, with <code class="docutils literal notranslate"><span class="pre">-</span></code> replaced by <code class="docutils literal notranslate"><span class="pre">_</span></code>). The value of the attribute will be a
single item list containing all the header values.</p>
<p>For example:
<code class="docutils literal notranslate"><span class="pre">http.request.header.custom_request_header</span> <span class="pre">=</span> <span class="pre">[&quot;&lt;value1&gt;&quot;,</span> <span class="pre">&quot;&lt;value2&gt;&quot;]</span></code></p>
</section>
<section id="response-headers">
<h4>Response headers<a class="headerlink" href="#response-headers" title="Permalink to this heading"></a></h4>
<p>To capture HTTP response headers as span attributes, set the environment variable
<code class="docutils literal notranslate"><span class="pre">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE</span></code> to a comma delimited list of HTTP header names,
or pass the <code class="docutils literal notranslate"><span class="pre">http_capture_headers_server_response</span></code> keyword argument to the <code class="docutils literal notranslate"><span class="pre">instrument_app</span></code> method.</p>
<p>For example using the environment variable,</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE</span><span class="o">=</span><span class="s2">&quot;content-type,custom_response_header&quot;</span>
</pre></div>
</div>
<p>will extract <code class="docutils literal notranslate"><span class="pre">content-type</span></code> and <code class="docutils literal notranslate"><span class="pre">custom_response_header</span></code> from the response headers and add them as span attributes.</p>
<p>Response header names in FastAPI are case-insensitive. So, giving the header name as <code class="docutils literal notranslate"><span class="pre">CUStom-Header</span></code> in the environment
variable will capture the header named <code class="docutils literal notranslate"><span class="pre">custom-header</span></code>.</p>
<p>Regular expressions may also be used to match multiple headers that correspond to the given pattern.  For example:</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE</span><span class="o">=</span><span class="s2">&quot;Content.*,X-.*&quot;</span>
</pre></div>
</div>
<p>Would match all response headers that start with <code class="docutils literal notranslate"><span class="pre">Content</span></code> and <code class="docutils literal notranslate"><span class="pre">X-</span></code>.</p>
<p>To capture all response headers, set <code class="docutils literal notranslate"><span class="pre">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE</span></code> to <code class="docutils literal notranslate"><span class="pre">&quot;.*&quot;</span></code>.</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_RESPONSE</span><span class="o">=</span><span class="s2">&quot;.*&quot;</span>
</pre></div>
</div>
<p>The name of the added span attribute will follow the format <code class="docutils literal notranslate"><span class="pre">http.response.header.&lt;header_name&gt;</span></code> where <code class="docutils literal notranslate"><span class="pre">&lt;header_name&gt;</span></code>
is the normalized HTTP header name (lowercase, with <code class="docutils literal notranslate"><span class="pre">-</span></code> replaced by <code class="docutils literal notranslate"><span class="pre">_</span></code>). The value of the attribute will be a
list containing the header values.</p>
<p>For example:
<code class="docutils literal notranslate"><span class="pre">http.response.header.custom_response_header</span> <span class="pre">=</span> <span class="pre">[&quot;&lt;value1&gt;&quot;,</span> <span class="pre">&quot;&lt;value2&gt;&quot;]</span></code></p>
</section>
<section id="sanitizing-headers">
<h4>Sanitizing headers<a class="headerlink" href="#sanitizing-headers" title="Permalink to this heading"></a></h4>
<p>In order to prevent storing sensitive data such as personally identifiable information (PII), session keys, passwords,
etc, set the environment variable <code class="docutils literal notranslate"><span class="pre">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS</span></code>
to a comma delimited list of HTTP header names to be sanitized, or pass the <code class="docutils literal notranslate"><span class="pre">http_capture_headers_sanitize_fields</span></code>
keyword argument to the <code class="docutils literal notranslate"><span class="pre">instrument_app</span></code> method.</p>
<p>Regexes may be used, and all header names will be matched in a case-insensitive manner.</p>
<p>For example using the environment variable,</p>
<div class="highlight-default notranslate"><div class="highlight"><pre><span></span><span class="n">export</span> <span class="n">OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SANITIZE_FIELDS</span><span class="o">=</span><span class="s2">&quot;.*session.*,set-cookie&quot;</span>
</pre></div>
</div>
<p>will replace the value of headers such as <code class="docutils literal notranslate"><span class="pre">session-id</span></code> and <code class="docutils literal notranslate"><span class="pre">set-cookie</span></code> with <code class="docutils literal notranslate"><span class="pre">[REDACTED]</span></code> in the span.</p>
<div class="admonition note">
<p class="admonition-title">Note</p>
<p>The environment variable names used to capture HTTP headers are still experimental, and thus are subject to change.</p>
</div>
</section>
</section>
<section id="id1">
<h3>API<a class="headerlink" href="#id1" title="Permalink to this heading"></a></h3>
</section>
<dl class="py class">
<dt class="sig sig-object py" id="opentelemetry.instrumentation.fastapi.FastAPIInstrumentor">
<em class="property"><span class="pre">class</span><span class="w"> </span></em><span class="sig-prename descclassname"><span class="pre">opentelemetry.instrumentation.fastapi.</span></span><span class="sig-name descname"><span class="pre">FastAPIInstrumentor</span></span><span class="sig-paren">(</span><em class="sig-param"><span class="o"><span class="pre">*</span></span><span class="n"><span class="pre">args</span></span></em>, <em class="sig-param"><span class="o"><span class="pre">**</span></span><span class="n"><span class="pre">kwargs</span></span></em><span class="sig-paren">)</span><a class="reference internal" href="../../_modules/opentelemetry/instrumentation/fastapi.html#FastAPIInstrumentor"><span class="viewcode-link"><span class="pre">[source]</span></span></a><a class="headerlink" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor" title="Permalink to this definition"></a></dt>
<dd><p>Bases: <a class="reference internal" href="../base/instrumentor.html#opentelemetry.instrumentation.instrumentor.BaseInstrumentor" title="opentelemetry.instrumentation.instrumentor.BaseInstrumentor"><code class="xref py py-class docutils literal notranslate"><span class="pre">BaseInstrumentor</span></code></a></p>
<p>An instrumentor for FastAPI</p>
<p>See <cite>BaseInstrumentor</cite></p>
<dl class="py method">
<dt class="sig sig-object py" id="opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app">
<em class="property"><span class="pre">static</span><span class="w"> </span></em><span class="sig-name descname"><span class="pre">instrument_app</span></span><span class="sig-paren">(</span><em class="sig-param"><span class="n"><span class="pre">app</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">server_request_hook</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">client_request_hook</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">client_response_hook</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">tracer_provider</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">meter_provider</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">excluded_urls</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">http_capture_headers_server_request</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">http_capture_headers_server_response</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">http_capture_headers_sanitize_fields</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em>, <em class="sig-param"><span class="n"><span class="pre">exclude_spans</span></span><span class="o"><span class="pre">=</span></span><span class="default_value"><span class="pre">None</span></span></em><span class="sig-paren">)</span><a class="reference internal" href="../../_modules/opentelemetry/instrumentation/fastapi.html#FastAPIInstrumentor.instrument_app"><span class="viewcode-link"><span class="pre">[source]</span></span></a><a class="headerlink" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app" title="Permalink to this definition"></a></dt>
<dd><p>Instrument an uninstrumented FastAPI application.</p>
<dl class="field-list simple">
<dt class="field-odd">Parameters<span class="colon">:</span></dt>
<dd class="field-odd"><ul class="simple">
<li><p><strong>app</strong> (<span class="sphinx_autodoc_typehints-type"><code class="xref py py-class docutils literal notranslate"><span class="pre">FastAPI</span></code></span>) – The fastapi ASGI application callable to forward requests to.</p></li>
<li><p><strong>server_request_hook</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Callable" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Callable</span></code></a>[[<a class="reference external" href="https://opentelemetry-python.readthedocs.io/en/latest/api/trace.span.html#opentelemetry.trace.span.Span" title="(in OpenTelemetry Python)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Span</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Dict" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Dict</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Any" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Any</span></code></a>]], <a class="reference external" href="https://docs.python.org/3/library/constants.html#None" title="(in Python v3.14)"><code class="xref py py-obj docutils literal notranslate"><span class="pre">None</span></code></a>]]</span>) – Optional callback which is called with the server span and ASGI
scope object for every incoming request.</p></li>
<li><p><strong>client_request_hook</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Callable" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Callable</span></code></a>[[<a class="reference external" href="https://opentelemetry-python.readthedocs.io/en/latest/api/trace.span.html#opentelemetry.trace.span.Span" title="(in OpenTelemetry Python)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Span</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Dict" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Dict</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Any" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Any</span></code></a>], <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Dict" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Dict</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Any" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Any</span></code></a>]], <a class="reference external" href="https://docs.python.org/3/library/constants.html#None" title="(in Python v3.14)"><code class="xref py py-obj docutils literal notranslate"><span class="pre">None</span></code></a>]]</span>) – Optional callback which is called with the internal span, and ASGI
scope and event which are sent as dictionaries for when the method receive is called.</p></li>
<li><p><strong>client_response_hook</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Callable" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Callable</span></code></a>[[<a class="reference external" href="https://opentelemetry-python.readthedocs.io/en/latest/api/trace.span.html#opentelemetry.trace.span.Span" title="(in OpenTelemetry Python)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Span</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Dict" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Dict</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Any" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Any</span></code></a>], <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Dict" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Dict</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>, <a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Any" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Any</span></code></a>]], <a class="reference external" href="https://docs.python.org/3/library/constants.html#None" title="(in Python v3.14)"><code class="xref py py-obj docutils literal notranslate"><span class="pre">None</span></code></a>]]</span>) – Optional callback which is called with the internal span, and ASGI
scope and event which are sent as dictionaries for when the method send is called.</p></li>
<li><p><strong>tracer_provider</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://opentelemetry-python.readthedocs.io/en/latest/api/trace.html#opentelemetry.trace.TracerProvider" title="(in OpenTelemetry Python)"><code class="xref py py-class docutils literal notranslate"><span class="pre">TracerProvider</span></code></a>]</span>) – The optional tracer provider to use. If omitted
the current globally configured one is used.</p></li>
<li><p><strong>meter_provider</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://opentelemetry-python.readthedocs.io/en/latest/api/metrics.html#opentelemetry.metrics.MeterProvider" title="(in OpenTelemetry Python)"><code class="xref py py-class docutils literal notranslate"><span class="pre">MeterProvider</span></code></a>]</span>) – The optional meter provider to use. If omitted
the current globally configured one is used.</p></li>
<li><p><strong>excluded_urls</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>]</span>) – Optional comma delimited string of regexes to match URLs that should not be traced.</p></li>
<li><p><strong>http_capture_headers_server_request</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#list" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">list</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>]]</span>) – Optional list of HTTP headers to capture from the request.</p></li>
<li><p><strong>http_capture_headers_server_response</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#list" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">list</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>]]</span>) – Optional list of HTTP headers to capture from the response.</p></li>
<li><p><strong>http_capture_headers_sanitize_fields</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#list" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">list</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>]]</span>) – Optional list of HTTP headers to sanitize.</p></li>
<li><p><strong>exclude_spans</strong> (<span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Optional" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Optional</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#list" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">list</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Literal" title="(in Python v3.14)"><code class="xref py py-data docutils literal notranslate"><span class="pre">Literal</span></code></a>[<code class="docutils literal notranslate"><span class="pre">'receive'</span></code>, <code class="docutils literal notranslate"><span class="pre">'send'</span></code>]]]</span>) – Optionally exclude HTTP <cite>send</cite> and/or <cite>receive</cite> spans from the trace.</p></li>
</ul>
</dd>
</dl>
</dd></dl>

<dl class="py method">
<dt class="sig sig-object py" id="opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.uninstrument_app">
<em class="property"><span class="pre">static</span><span class="w"> </span></em><span class="sig-name descname"><span class="pre">uninstrument_app</span></span><span class="sig-paren">(</span><em class="sig-param"><span class="n"><span class="pre">app</span></span></em><span class="sig-paren">)</span><a class="reference internal" href="../../_modules/opentelemetry/instrumentation/fastapi.html#FastAPIInstrumentor.uninstrument_app"><span class="viewcode-link"><span class="pre">[source]</span></span></a><a class="headerlink" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.uninstrument_app" title="Permalink to this definition"></a></dt>
<dd></dd></dl>

<dl class="py method">
<dt class="sig sig-object py" id="opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrumentation_dependencies">
<span class="sig-name descname"><span class="pre">instrumentation_dependencies</span></span><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="reference internal" href="../../_modules/opentelemetry/instrumentation/fastapi.html#FastAPIInstrumentor.instrumentation_dependencies"><span class="viewcode-link"><span class="pre">[source]</span></span></a><a class="headerlink" href="#opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrumentation_dependencies" title="Permalink to this definition"></a></dt>
<dd><p>Return a list of python packages with versions that the will be instrumented.</p>
<p>The format should be the same as used in requirements.txt or pyproject.toml.</p>
<p>For example, if an instrumentation instruments requests 1.x, this method should look
like:
:rtype: <span class="sphinx_autodoc_typehints-type"><a class="reference external" href="https://docs.python.org/3/library/typing.html#typing.Collection" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">Collection</span></code></a>[<a class="reference external" href="https://docs.python.org/3/library/stdtypes.html#str" title="(in Python v3.14)"><code class="xref py py-class docutils literal notranslate"><span class="pre">str</span></code></a>]</span></p>
<blockquote>
<div><dl class="simple">
<dt>def instrumentation_dependencies(self) -&gt; Collection[str]:</dt><dd><p>return [‘requests ~= 1.0’]</p>
</dd>
</dl>
</div></blockquote>
<p>This will ensure that the instrumentation will only be used when the specified library
is present in the environment.</p>
</dd></dl>

</dd></dl>

</section>
</section>


           </div>
          </div>
          <footer><div class="rst-footer-buttons" role="navigation" aria-label="Footer">
        <a href="../falcon/falcon.html" class="btn btn-neutral float-left" title="OpenTelemetry Falcon Instrumentation" accesskey="p" rel="prev"><span class="fa fa-arrow-circle-left" aria-hidden="true"></span> Previous</a>
        <a href="../flask/flask.html" class="btn btn-neutral float-right" title="OpenTelemetry Flask Instrumentation" accesskey="n" rel="next">Next <span class="fa fa-arrow-circle-right" aria-hidden="true"></span></a>
    </div>

  <hr/>

  <div role="contentinfo">
    <p>&#169; Copyright OpenTelemetry Authors.</p>
  </div>

  Built with <a href="https://www.sphinx-doc.org/">Sphinx</a> using a
    <a href="https://github.com/readthedocs/sphinx_rtd_theme">theme</a>
    provided by <a href="https://readthedocs.org">Read the Docs</a>.
   

</footer>
        </div>
      </div>
    </section>
  </div>
  <script>
      jQuery(function () {
          SphinxRtdTheme.Navigation.enable(true);
      });
  </script> 

</body>
</html>