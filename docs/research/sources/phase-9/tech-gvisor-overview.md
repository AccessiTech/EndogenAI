<!-- fetch_source.py metadata
url: https://gvisor.dev/docs/
fetched: 2026-03-04T18:12:51Z
http_status: 200
-->
# Fetched source: https://gvisor.dev/docs/
_Fetched: 2026-03-04T18:12:51Z | HTTP 200_

---

<!DOCTYPE html>
<html lang="en" itemscope itemtype="https://schema.org/WebPage">
    <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <title> What is gVisor? - gVisor</title>
    
    <link rel="canonical" href="/docs/">

    <!-- Dependencies. -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha256-916EbMg70RQy9LHiGkXzG8hSg9EdNy97GazNG/aiY1w=" crossorigin="anonymous" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.10.1/css/all.min.css" integrity="sha256-fdcFNFiBMrNfWL6OcAGQz6jDgNTRxnrLEd4vJYFWScE=" crossorigin="anonymous" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.10.1/js/all.min.js" integrity="sha256-Z1Nvg/+y2+vRFhFgFij7Lv0r77yG3hOvWz2wI0SfTa0=" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha256-U5ZEeKfGNOja007MMD3YBI0A3OSZOQbeG6z2f2Y0hu8=" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.13.0/d3.min.js" integrity="sha256-hYXbQJK4qdJiAeDVjjQ9G0D6A0xLnDQ4eJI9dkm7Fpk=" crossorigin="anonymous"></script>


    <!-- Our own style sheet. -->
    <link rel="stylesheet" type="text/css" href="/css/main.css">
    <link rel="icon" type="image/png" href="/assets/favicons/favicon-32x32.png" sizes="32x32">
    <link rel="icon" type="image/png" href="/assets/favicons/favicon-16x16.png" sizes="16x16">

    
    <meta name="og:title" content=" What is gVisor?">
    
    
    <meta name="og:image" content="https://gvisor.dev/assets/logos/logo_solo_on_white_bordered.svg">
  </head>

  <body>
    <nav class="navbar navbar-expand-sm navbar-inverse navbar-fixed-top">
  <div class="container">
    <div class="navbar-brand">
      <a href="/">
        <img src="/assets/logos/logo_solo_on_dark.svg" height="25" class="d-inline-block align-top" style="margin-right: 10px;" alt="logo" />
        gVisor
      </a>
    </div>

    <div class="collapse navbar-collapse">
      <ul class="nav navbar-nav navbar-right">
        <li><a href="/docs">Documentation</a></li>
        <li><a href="/blog">Blog</a></li>
        <li><a href="/users">Users</a></li>
        <li><a href="/community/">Community</a></li>
        <li><a href="https://github.com/google/gvisor">GitHub</a></li>
      </ul>
    </div>
  </div>
</nav>

    <div class="container">
  <div class="row">
    <div class="col-md-3">
      <nav class="sidebar" id="sidebar-nav">
        
          <h3>Project</h3>
          <ul class="sidebar-nav">
          
          
            
            
            
              
              
                <li class="active"><a href="/docs/"> What is gVisor?</a></li>
              
                <li><a href="/roadmap/"> Roadmap</a></li>
              
                <li><a href="/contributing/"> Contributing</a></li>
              
                <li><a href="/security/"> Security and Vulnerability Reporting</a></li>
              
              
            
          
            
            
            
              
                
                
                <li>
                  
                  
                  
                  <a class="sidebar-nav-heading" data-toggle="collapse" href="#project-community" aria-expanded="false" aria-controls="project-community">Community<span class="caret"></span></a>
                  <ul class="collapse sidebar-nav sidebar-submenu" id="project-community">
              
              
                <li><a href="/community/"> Participation</a></li>
              
                <li><a href="/community/governance/"> Governance</a></li>
              
                <li><a href="/community/code_of_conduct/"> Code of Conduct</a></li>
              
                <li><a href="/community/style_guide/"> Provisional style guide</a></li>
              
              
                </li>
              </ul>
              
            
          
          </ul>
        
          <h3>User Guide</h3>
          <ul class="sidebar-nav">
          
          
            
            
            
              
              
                <li><a href="/docs/user_guide/install/"> Installation</a></li>
              
                <li><a href="/docs/user_guide/production/"> Production guide</a></li>
              
                <li><a href="/docs/user_guide/platforms/"> Changing Platforms</a></li>
              
                <li><a href="/docs/user_guide/filesystem/"> Filesystem</a></li>
              
                <li><a href="/docs/user_guide/networking/"> Networking</a></li>
              
                <li><a href="/docs/user_guide/gpu/"> GPU Support</a></li>
              
                <li><a href="/docs/user_guide/tpu/"> TPU Support</a></li>
              
                <li><a href="/docs/user_guide/runtimemonitor/"> Runtime Monitoring</a></li>
              
                <li><a href="/docs/user_guide/observability/"> Observability</a></li>
              
                <li><a href="/docs/user_guide/checkpoint_restore/"> Checkpoint/Restore</a></li>
              
                <li><a href="/docs/user_guide/debugging/"> Debugging</a></li>
              
                <li><a href="/docs/user_guide/faq/"> FAQ</a></li>
              
                <li><a href="/docs/user_guide/systemd/"> Systemd cgroup driver</a></li>
              
                <li><a href="/docs/user_guide/rootfs_snapshot/"> Rootfs Snapshot</a></li>
              
              
            
          
            
            
            
              
                
                
                <li>
                  
                  
                  
                  <a class="sidebar-nav-heading" data-toggle="collapse" href="#userguide-containerd" aria-expanded="false" aria-controls="userguide-containerd">Containerd<span class="caret"></span></a>
                  <ul class="collapse sidebar-nav sidebar-submenu" id="userguide-containerd">
              
              
                <li><a href="/docs/user_guide/containerd/quick_start/"> Containerd Quick Start</a></li>
              
                <li><a href="/docs/user_guide/containerd/configuration/"> Containerd Advanced Configuration</a></li>
              
              
                </li>
              </ul>
              
            
          
            
            
            
              
                
                
                <li>
                  
                  
                  
                  <a class="sidebar-nav-heading" data-toggle="collapse" href="#userguide-quickstart" aria-expanded="false" aria-controls="userguide-quickstart">Quick Start<span class="caret"></span></a>
                  <ul class="collapse sidebar-nav sidebar-submenu" id="userguide-quickstart">
              
              
                <li><a href="/docs/user_guide/quick_start/docker/"> Docker Quick Start</a></li>
              
                <li><a href="/docs/user_guide/quick_start/kubernetes/"> Kubernetes Quick Start</a></li>
              
                <li><a href="/docs/user_guide/quick_start/oci/"> OCI Quick Start</a></li>
              
              
                </li>
              </ul>
              
            
          
            
            
            
              
                
                
                <li>
                  
                  
                  
                  <a class="sidebar-nav-heading" data-toggle="collapse" href="#userguide-tutorials" aria-expanded="false" aria-controls="userguide-tutorials">Tutorials<span class="caret"></span></a>
                  <ul class="collapse sidebar-nav sidebar-submenu" id="userguide-tutorials">
              
              
                <li><a href="/docs/tutorials/docker/"> WordPress with Docker</a></li>
              
                <li><a href="/docs/tutorials/docker-compose/"> Wordpress with Docker Compose</a></li>
              
                <li><a href="/docs/tutorials/kubernetes/"> WordPress with Kubernetes</a></li>
              
                <li><a href="/docs/tutorials/falco/"> Configuring Falco with gVisor</a></li>
              
                <li><a href="/docs/tutorials/knative/"> Knative Services</a></li>
              
                <li><a href="/docs/tutorials/docker-in-gvisor/"> Docker in gVisor</a></li>
              
                <li><a href="/docs/tutorials/docker-in-gke-sandbox/"> Docker in a GKE sandbox</a></li>
              
                <li><a href="/docs/tutorials/cni/"> Using CNI</a></li>
              
              
                </li>
              </ul>
              
            
          
          </ul>
        
          <h3>Architecture Guide</h3>
          <ul class="sidebar-nav">
          
          
            
            
            
              
              
                <li><a href="/docs/architecture_guide/intro/"> Introduction to gVisor security</a></li>
              
                <li><a href="/docs/architecture_guide/security/"> Security Model</a></li>
              
                <li><a href="/docs/architecture_guide/resources/"> Resource Model</a></li>
              
                <li><a href="/docs/architecture_guide/platforms/"> Platform Guide</a></li>
              
                <li><a href="/docs/architecture_guide/performance/"> Performance Guide</a></li>
              
                <li><a href="/docs/architecture_guide/networking/"> Networking Guide</a></li>
              
              
            
          
          </ul>
        
          <h3>Compatibility</h3>
          <ul class="sidebar-nav">
          
          
            
            
            
              
              
                <li><a href="/docs/user_guide/compatibility/"> Applications</a></li>
              
                <li><a href="/docs/user_guide/compatibility/linux/arm64/">Linux/arm64</a></li>
              
                <li><a href="/docs/user_guide/compatibility/linux/amd64/">Linux/amd64</a></li>
              
              
            
          
          </ul>
        
      </nav>
    </div>

    <div class="col-md-9">
      <h1> What is gVisor?</h1>
      
        <p>
        <a href="https://github.com/google/gvisor/edit/master/g3doc/README.md" target="_blank" rel="noopener"><i class="fa fa-edit fa-fw"></i> Edit this page</a>
        <a href="https://github.com/google/gvisor/issues/new?title=+What+is+gVisor%3F" target="_blank" rel="noopener"><i class="fab fa-github fa-fw"></i> Create issue</a>
        </p>
      
      <div class="docs-content">
      <p><strong>gVisor</strong> provides a strong layer of isolation between running applications and
the host operating system. It is an application kernel that implements a
<a href="https://en.wikipedia.org/wiki/Linux_kernel_interfaces">Linux-like interface</a>. Unlike Linux, it is written in a memory-safe
language (Go) and runs in userspace.</p>

<p>gVisor includes an <a href="https://www.opencontainers.org">Open Container Initiative (OCI)</a> runtime called <code class="highlighter-rouge">runsc</code>
that makes it easy to work with existing container tooling. The <code class="highlighter-rouge">runsc</code> runtime
integrates with Docker and Kubernetes, making it simple to run sandboxed
containers.</p>

<p>gVisor can be used with Docker, Kubernetes, or directly using <code class="highlighter-rouge">runsc</code>. Use the
links below to see detailed instructions for each of them:</p>

<ul>
  <li><a href="/docs/user_guide/quick_start/docker/">Docker</a>: The quickest and easiest way
to get started.</li>
  <li><a href="/docs/user_guide/quick_start/kubernetes/">Kubernetes</a>: Isolate Pods in your
K8s cluster with gVisor.</li>
  <li><a href="/docs/user_guide/quick_start/oci/">OCI Quick Start</a>: Expert mode. Customize
gVisor for your environment.</li>
</ul>

<h2 id="what-does-gvisor-do">What does gVisor do?</h2>

<p>gVisor provides a virtualized environment in order to sandbox containers. The
system interfaces normally implemented by the host kernel are moved into a
distinct, per-sandbox application kernel in order to minimize the risk of a
container escape exploit. gVisor does not introduce large fixed overheads
however, and still retains a process-like model with respect to resource
utilization.</p>

<h2 id="how-is-this-different">How is this different?</h2>

<p>Two other approaches are commonly taken to provide stronger isolation than
native containers.</p>

<ul>
  <li>gVisor is <strong>not a syscall filter</strong> (e.g. <code class="highlighter-rouge">seccomp-bpf</code>), nor a wrapper over
Linux isolation primitives (e.g. <code class="highlighter-rouge">firejail</code>, AppArmor, etc.).</li>
  <li>gVisor is also <strong>not a VM</strong> in the everyday sense of the term (e.g.
VirtualBox, QEMU).</li>
</ul>

<p><strong>gVisor takes a distinct third approach</strong>, providing many security benefits of
VMs while maintaining the lower resource footprint, fast startup, and
flexibility of regular userspace applications.</p>

<p>Let’s take a closer look.</p>

<p><strong>Machine-level virtualization</strong>, such as <a href="https://www.linux-kvm.org">KVM</a> and <a href="https://www.xenproject.org">Xen</a>, exposes
virtualized hardware to a guest kernel via a Virtual Machine Monitor (VMM). This
virtualized hardware is generally enlightened (paravirtualized) and additional
mechanisms can be used to improve the visibility between the guest and host
(e.g. balloon drivers, paravirtualized spinlocks). Running containers in
distinct virtual machines can provide great isolation, compatibility and
performance (though nested virtualization may bring challenges in this area),
but for containers it often requires additional proxies and agents, and may
require a larger resource footprint and slower start-up times.</p>

<p><img src="Machine-Virtualization.png" alt="Machine-level virtualization" title="Machine-level virtualization" /></p>

<p><strong>Rule-based execution</strong>, such as <a href="https://www.kernel.org/doc/Documentation/prctl/seccomp_filter.txt">seccomp</a>, <a href="https://selinuxproject.org">SELinux</a> and
<a href="https://wiki.ubuntu.com/AppArmor">AppArmor</a>, allows the specification of a fine-grained security policy
for an application or container. These schemes typically rely on hooks
implemented inside the host kernel to enforce the rules. If the surface can be
made small enough, then this is an excellent way to sandbox applications and
maintain native performance. However, in practice it can be extremely difficult
(if not impossible) to reliably define a policy for arbitrary, previously
unknown applications, making this approach challenging to apply universally.</p>

<p><img src="Rule-Based-Execution.png" alt="Rule-based execution" title="Rule-based execution" /></p>

<p>Rule-based execution is often combined with additional layers for
defense-in-depth.</p>

<p><strong>gVisor</strong> provides a third isolation mechanism, distinct from those above.</p>

<p>gVisor intercepts application system calls and acts as the guest kernel, without
the need for translation through virtualized hardware. gVisor may be thought of
as either a merged guest kernel and VMM, or as seccomp on steroids. This
architecture allows it to provide a flexible resource footprint (i.e. one based
on threads and memory mappings, not fixed guest physical resources) while also
lowering the fixed costs of virtualization. However, this comes at the price of
reduced application compatibility and higher per-system call overhead.</p>

<p><img src="Layers.png" alt="gVisor" title="gVisor" /></p>

<p>On top of this, gVisor employs rule-based execution to provide defense-in-depth
(details below).</p>

<p>gVisor’s approach is similar to <a href="http://user-mode-linux.sourceforge.net/">User Mode Linux (UML)</a>, although UML
virtualizes hardware internally and thus provides a fixed resource footprint.</p>

<p>Each of the above approaches may excel in distinct scenarios. For example,
machine-level virtualization will face challenges achieving high density, while
gVisor may provide poor performance for system call heavy workloads.</p>

<h2 id="why-go">Why Go?</h2>

<p>gVisor is written in <a href="https://golang.org">Go</a> in order to avoid security pitfalls that can
plague kernels. With Go, there are strong types, built-in bounds checks, no
uninitialized variables, no use-after-free, no stack overflow, and a built-in
race detector. However, the use of Go has its challenges, and the runtime often
introduces performance overhead.</p>

<h2 id="what-are-the-different-components">What are the different components?</h2>

<p>A gVisor sandbox consists of multiple processes. These processes collectively
comprise an environment in which one or more containers can be run.</p>

<p>Each sandbox has its own isolated instance of:</p>

<ul>
  <li>The <strong>Sentry</strong>, which is a kernel that runs the containers and intercepts
and responds to system calls made by the application.</li>
</ul>

<p>Each container running in the sandbox has its own isolated instance of:</p>

<ul>
  <li>A <strong>Gofer</strong> which provides file system access to the containers.</li>
</ul>

<p><img src="Sentry-Gofer.png" alt="gVisor architecture diagram" title="gVisor architecture diagram" /></p>

<h2 id="what-is-runsc">What is runsc?</h2>

<p>The entrypoint to running a sandboxed container is the <code class="highlighter-rouge">runsc</code> executable.
<code class="highlighter-rouge">runsc</code> implements the <a href="https://www.opencontainers.org">Open Container Initiative (OCI)</a> runtime
specification, which is used by Docker and Kubernetes. This means that OCI
compatible <em>filesystem bundles</em> can be run by <code class="highlighter-rouge">runsc</code>. Filesystem bundles are
comprised of a <code class="highlighter-rouge">config.json</code> file containing container configuration, and a root
filesystem for the container. Please see the <a href="https://github.com/opencontainers/runtime-spec">OCI runtime spec</a>
for more information on filesystem bundles. <code class="highlighter-rouge">runsc</code> implements multiple commands
that perform various functions such as starting, stopping, listing, and querying
the status of containers.</p>

<h3 id="sentry">Sentry</h3>

<p>The Sentry is the largest component of gVisor. It can be thought of as a
application kernel. The Sentry implements all the kernel functionality needed by
the application, including: system calls, signal delivery, memory management and
page faulting logic, the threading model, and more.</p>

<p>When the application makes a system call, the
<a href="/docs/architecture_guide/platforms/">Platform</a> redirects the call to the Sentry,
which will do the necessary work to service it. It is important to note that the
Sentry does not pass system calls through to the host kernel. As a userspace
application, the Sentry will make some host system calls to support its
operation, but it does not allow the application to directly control the system
calls it makes. For example, the Sentry is not able to open files directly; file
system operations that extend beyond the sandbox (not internal <code class="highlighter-rouge">/proc</code> files,
pipes, etc) are sent to the Gofer, described below.</p>

<h3 id="gofer">Gofer</h3>

<p>The Gofer is a standard host process which is started with each container and
communicates with the Sentry via the <a href="https://en.wikipedia.org/wiki/9P_(protocol)">9P protocol</a> over a socket or shared
memory channel. The Sentry process is started in a restricted seccomp container
without access to file system resources. The Gofer mediates all access to these
resources, providing an additional level of isolation.</p>

<h3 id="application">Application</h3>

<p>The application is a normal Linux binary provided to gVisor in an OCI runtime
bundle. gVisor aims to provide an environment equivalent to Linux v4.4, so
applications should be able to run unmodified. However, gVisor does not
presently implement every system call, <code class="highlighter-rouge">/proc</code> file, or <code class="highlighter-rouge">/sys</code> file so some
incompatibilities may occur. See <a href="/docs/user_guide/compatibility/">Compatibility</a>
for more information.</p>


      </div>
    </div>
  </div>
</div>

    <footer class="footer">
  <div class="container">
  <div class="row">
    <div class="col-sm-3 col-md-2">
      <p>About</p>
      <ul class="list-unstyled">
        <li><a href="/roadmap/">Roadmap</a></li>
        <li><a href="/contributing/">Contributing</a></li>
        <li><a href="/security/">Security</a></li>
        <li><a href="/community/governance/">Governance</a></li>
        <li><a href="https://policies.google.com/privacy">Privacy Policy</a></li>
      </ul>
    </div>
    <div class="col-sm-3 col-md-2">
      <p>Support</p>
      <ul class="list-unstyled">
        <li><a href="https://github.com/google/gvisor/issues">Issues</a></li>
        <li><a href="/docs">Documentation</a></li>
        <li><a href="/docs/user_guide/faq">FAQ</a></li>
      </ul>
    </div>
    <div class="col-sm-3 col-md-2">
      <p>Connect</p>
      <ul class="list-unstyled">
        <li><a href="https://github.com/google/gvisor">GitHub</a></li>
        <li><a href="https://groups.google.com/forum/#!forum/gvisor-users">User Mailing List</a></li>
        <li><a href="https://groups.google.com/forum/#!forum/gvisor-dev">Developer Mailing List</a></li>
        <li><a href="https://gitter.im/gvisor/community">Gitter Chat</a></li>
        <li><a href="/blog">Blog</a></li>
      </ul>
    </div>
    <div class="col-sm-3 col-md-3"></div>
    <div class="hidden-xs hidden-sm col-md-3">
      <a href="https://cloud.google.com/run">
        <img style="float: right; max-width: 93px; height: auto;" src="/assets/logos/powered-gvisor.png" alt="Powered by gVisor"/>
      </a>
    </div>
  </div>
  <div class="row">
    <div class="col-lg-12">
      <p>&copy; 2026 The gVisor Authors</p>
    </div>
  </div>
</div>

</footer>


<script>
var doNotTrack = false;
if (!doNotTrack) {
  window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
  ga('create', 'UA-150193582-1', 'auto');
  ga('send', 'pageview');
}
</script>
<script async src='https://www.google-analytics.com/analytics.js'></script>


<script>
  var shiftWindow = function() {
    if (location.hash.length !== 0) {
      window.scrollBy(0, -50);
    }
  };
  window.addEventListener("hashchange", shiftWindow);

  $(document).ready(function() {
    // Scroll to anchor of location hash, adjusted for fixed navbar.
    window.setTimeout(function() {
      shiftWindow();
    }, 1);

    // Flip the caret when submenu toggles are clicked.
    $(".sidebar-submenu").on("show.bs.collapse", function() {
      var toggle = $('[href$="#' + $(this).attr('id') + '"]');
      if (toggle) {
        toggle.addClass("dropup");
      }
    });
    $(".sidebar-submenu").on("hide.bs.collapse", function() {
      var toggle = $('[href$="#' + $(this).attr('id') + '"]');
      if (toggle) {
        toggle.removeClass("dropup");
      }
    });
  });
</script>

  </body>
</html>
