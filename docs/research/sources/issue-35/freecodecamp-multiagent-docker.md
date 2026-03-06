<!-- fetch_source.py metadata
url: https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/
fetched: 2026-03-06T18:28:31Z
http_status: 200
-->
# Fetched source: https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/
_Fetched: 2026-03-06T18:28:31Z | HTTP 200_

---

<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        
        
            <title>How to Build and Deploy a Multi-Agent AI System with Python and Docker</title>
        
        <meta name="HandheldFriendly" content="True">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
        <link rel="preload" as="style" onload="this.onload=null;this.rel='stylesheet'" href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,300;0,400;0,700;1,400&family=Roboto+Mono:wght@400;700&display=swap">
        

        
        
    <link rel="preload" as="style" onload="this.onload=null;this.rel='stylesheet'" href="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/themes/prism.min.css">
<noscript>
  <link rel="stylesheet" href="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/themes/prism.min.css">
</noscript>
<link rel="preload" as="style" onload="this.onload=null;this.rel='stylesheet'" href="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/plugins/unescaped-markup/prism-unescaped-markup.min.css">
<noscript>
  <link rel="stylesheet" href="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/plugins/unescaped-markup/prism-unescaped-markup.min.css">
</noscript>

<script defer="" src="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/components/prism-core.min.js"></script>
<script defer="" src="https://cdn.freecodecamp.org/news-assets/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>



        
        <link rel="preload" as="style" onload="this.onload=null;this.rel='stylesheet'" href="/news/assets/css/global-a1e6959968.css">
        <link rel="stylesheet" type="text/css" href="/news/assets/css/variables-b2e544cd65.css">
        <link rel="stylesheet" type="text/css" href="/news/assets/css/screen-d1c41ea162.css">
        <link rel="stylesheet" type="text/css" href="/news/assets/css/search-bar-cd71311c1d.css">

        
        <script defer="" src="https://cdn.freecodecamp.org/news-assets/algolia/algoliasearch/5.46.3/lite/browser.umd.js"></script>
        <script defer="" src="https://cdn.freecodecamp.org/news-assets/algolia/autocomplete/1.19.4/index.production.min.js"></script>
        
        
        <script defer="" src="https://cdn.freecodecamp.org/news-assets/dayjs/1.10.4/dayjs.min.js"></script>
        <script defer="" src="https://cdn.freecodecamp.org/news-assets/dayjs/1.10.4/localizedFormat.min.js"></script>
        <script defer="" src="https://cdn.freecodecamp.org/news-assets/dayjs/1.10.4/relativeTime.min.js"></script>

        
        
            <script defer="" src="https://cdn.freecodecamp.org/news-assets/dayjs/1.10.4/locale/en.min.js"></script>
        

        
        <script>document.addEventListener("DOMContentLoaded",async()=>{const{liteClient:e}=window["algoliasearch/lite"],{autocomplete:t,getAlgoliaResults:n}=window["@algolia/autocomplete-js"],a=e("QMJYL5WYTI","89770b24481654192d7a5c402c6ad9a0"),o=window.screen.width>=767&&window.screen.height>=768?8:5,s=((e,t)=>{let n;return(...a)=>(n&&clearTimeout(n),new Promise(o=>{n=setTimeout(()=>o(e(...a)),t)}))})(e=>Promise.resolve(e),200),r=e=>t({container:e,panelContainer:e,stallThreshold:500,detachedMediaQuery:"none",debug:!0,placeholder:Number("12400")<100?"Search our news articles, tutorials, and books":"Search 12,400+ news articles, tutorials, and books",getSources:()=>s([{sourceId:"links",getItemUrl:({item:e})=>e.url,getItems:({query:e})=>n({searchClient:a,queries:[{indexName:"news",params:{query:e,hitsPerPage:o}}]}),templates:{item:({item:e,components:t,html:n})=>n`<a class="aa-ItemLink" href=${e.url}>
                  <div class="aa-ItemContent">
                    <div class="aa-ItemContentBody">
                      <div class="aa-ItemContentTitle">
                        ${t.Highlight({hit:e,attribute:"title",tagName:"mark"})}
                      </div>
                    </div>
                  </div>
                </a>`,footer({state:e,html:t}){const n=e?.query,a=e?.collections[0]?.items;if(a.length)return t`<a
                    class="aa-ItemLink"
                    href="https://www.freecodecamp.org/news/search?query=${n}"
                    ><div class="aa-ItemContent">
                      See all results for ${n}
                    </div></a
                  >`},noResults:()=>"No results found"}}])}),i=r("#nav-left-search-container");r("#nav-right-search-container");const c=document.querySelectorAll(".fcc-search-container");document.addEventListener("keydown",e=>{e.target instanceof HTMLInputElement||e.target instanceof HTMLTextAreaElement||e.target.isContentEditable||"/"!==e.key&&"s"!==e.key||(e.preventDefault(),c.forEach(e=>{e.checkVisibility()&&e.querySelector("input").focus()}))}),c.forEach(e=>{e.addEventListener("submit",t=>{t.preventDefault();const n=e.querySelector("input").value.trim(),a=e.querySelector(".aa-List");n&&a&&window.location.assign(`https://www.freecodecamp.org/news/search?query=${n}`)})}),document.addEventListener("click",e=>{e.target!==document.querySelector("#nav-left-search-container .aa-Form")&&i.setIsOpen(!1)})}),document.addEventListener("DOMContentLoaded",()=>{dayjs.extend(dayjs_plugin_localizedFormat),dayjs.extend(dayjs_plugin_relativeTime),dayjs.locale("en")});const isAuthenticated=document.cookie.split(";").some(e=>e.trim().startsWith("jwt_access_token=")),isDonor=document.cookie.split(";").some(e=>e.trim().startsWith("isDonor=true"));document.addEventListener("DOMContentLoaded",()=>{document.getElementById("toggle-button-nav").addEventListener("click",function(){const e=document.getElementById("menu-dropdown"),t=document.getElementById("toggle-button-nav");e.classList.toggle("display-menu"),t.ariaExpanded="true"==t.ariaExpanded?"false":"true"})});</script>

        
            <script src="https://securepubads.g.doubleclick.net/tag/js/gpt.js" crossorigin="anonymous" async=""></script>
        

        
        
    
        
            <script>
document.addEventListener('DOMContentLoaded', function() {
    var sidebar = document.querySelector('.sidebar');
    var isSideBarDisplayed = window.getComputedStyle(sidebar).display !== 'none';
    function prepareAdSlot(elementId) {
        // Get the element by ID
        const targetElement = document.getElementById(elementId);

        // Ensure the element exists before proceeding
        if (!targetElement) {
            console.error(`Element with ID ${elementId} not found`);
            return;
        }

        const parentElement = targetElement.parentElement;
        // Change the background color of the parent element

        if (parentElement) {
            console.log(elementId)

            if (elementId === 'gam-ad-bottom' ) {
                parentElement.style.backgroundColor = '#eeeef0';
                if(getComputedStyle(parentElement).visibility === 'hidden') {
                    parentElement.style.visibility = 'inherit'; 
                }
            }

            // Get the sibling elements
            const siblingElements = parentElement.children;

            for (let i = 0; i < siblingElements.length; i++) {
                const sibling = siblingElements[i];

                // Skip the element itself
                if (sibling === targetElement) continue;

                // Log the sibling or perform any other action
                console.log('Found sibling:', sibling);

                // Check visibility
                if(getComputedStyle(sibling).visibility === 'hidden') {
                    sibling.style.visibility = 'inherit'; 
                }

                // Check if display is 'none', then change it to 'block'
                if (getComputedStyle(sibling).display === 'none') {
                    sibling.style.display = 'block'; 
                }
            }
        } else {
            console.warn('No parent element found');
        }
    }

    
    window.googletag = window.googletag || {cmd: []};
    googletag.cmd.push(function() {

        if(isSideBarDisplayed){
            var sidebarHeight = sidebar.offsetHeight;
            var adTextSideBarHeight = 0;
            var sideBarAdContainert = 600 + 17;
        
            var styles = window.getComputedStyle(sidebar);
            var avaiableSideAdSpace = sidebarHeight - adTextSideBarHeight - parseFloat(styles.paddingTop) - parseFloat(styles.paddingBottom);
            var numSideElements = Math.floor(avaiableSideAdSpace / sideBarAdContainert);
            for (var i = 0; i < numSideElements; i++) {
                // container element
                var containerElement = document.createElement('div');
                containerElement.classList.add('ad-wrapper');

                //text element
                var textElement = document.createElement('div');
                textElement.classList.add('ad-text');
                textElement.innerText = localizedAdText;

                // ad element
                var adElement = document.createElement('div');
                var sideAdElementId = 'side-gam-ad-' + i;
                adElement.id = sideAdElementId;
                adElement.classList.add('side-bar-ad-slot');

                // finalize setup
                containerElement.appendChild(textElement);
                containerElement.appendChild(adElement);
                sidebar.appendChild(containerElement);
                googletag.defineSlot('/23075930536/post-side', [[292, 30], [240, 400], [300, 75], [216, 54], [250, 360], [300, 50], 'fluid', [300, 31], [120, 20], [300, 250], [120, 30], [180, 150], [200, 446], [168, 42], [200, 200], [160, 600], [120, 90], [125, 125], [240, 133], [120, 60], [1, 1], [120, 240], [220, 90], [216, 36], [250, 250], [168, 28], [234, 60], [120, 600], [300, 600], [88, 31], [300, 100]], sideAdElementId).addService(googletag.pubads());
            }
        }

        // Define bottom ad
        googletag.defineSlot('/23075930536/post-bottom', ['fluid'], 'gam-ad-bottom').addService(googletag.pubads());

        // Enable lazy loading with default settings.
        googletag.pubads().enableLazyLoad();

        googletag.pubads().addEventListener("slotRequested", (event) => {
            console.log(`Slot ${event.slot.getSlotElementId()} fetched`);
        });

        googletag.pubads().addEventListener("slotOnload", (event) => {
            const elementId = event.slot.getSlotElementId();
            prepareAdSlot(elementId);
            console.log(`Slot ${event.slot.getSlotElementId()} rendered`);
        });

        googletag.pubads().enableSingleRequest();
        googletag.enableServices();


        // Trigger lazy loading
        googletag.display('gam-ad-bottom');

    });
});
</script>

        
    


        
            <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-5D6RKKP');</script>

        

        
        
    
        
    
        
    
        
    
        
    
        
    
        
    


        
        
        

        
        

        <link rel="icon" href="https://cdn.freecodecamp.org/universal/favicons/favicon.ico" type="image/png">
        
        
            <link rel="canonical" href="https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/">
        
        <meta name="referrer" content="no-referrer-when-downgrade">

        

        
    <meta name="description" content="You wake up and open your laptop. Your browser has 27 tabs open, your inbox is overflowing with unread newsletters, and meeting notes are scattered across three apps. Sound familiar? Now imagine you h">

    
    <meta property="og:site_name" content="freeCodeCamp.org">
    <meta property="og:type" content="article">
    <meta property="og:title" content="How to Build and Deploy a Multi-Agent AI System with Python and Docker">
    
        <meta property="og:description" content="You wake up and open your laptop. Your browser has 27 tabs open, your inbox is overflowing with unread newsletters, and meeting notes are scattered across three apps. Sound familiar? Now imagine you h">
    
    <meta property="og:url" content="https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/">
    <meta property="og:image" content="https://cloudmate-test.s3.us-east-1.amazonaws.com/uploads/covers/5fc16e412cae9c5b190b6cdd/6bd425e1-7427-4fe8-b1a7-80fff56102f7.png">
    <meta property="article:published_time" content="2026-02-23T15:55:01.909Z">
    <meta property="article:modified_time" content="2026-02-25T20:33:46.470Z">
    
        <meta property="article:tag" content="AI">
    
        <meta property="article:tag" content="Docker">
    
        <meta property="article:tag" content="Python">
    
        <meta property="article:tag" content="ollama">
    
        <meta property="article:tag" content="Open Source">
    
        <meta property="article:tag" content="handbook">
    
    <meta property="article:publisher" content="https://www.facebook.com/freecodecamp">
    

    
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="How to Build and Deploy a Multi-Agent AI System with Python and Docker">
    
        <meta name="twitter:description" content="You wake up and open your laptop. Your browser has 27 tabs open, your inbox is overflowing with unread newsletters, and meeting notes are scattered across three apps. Sound familiar? Now imagine you h">
    
    <meta name="twitter:url" content="https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/">
    <meta name="twitter:image" content="https://cloudmate-test.s3.us-east-1.amazonaws.com/uploads/covers/5fc16e412cae9c5b190b6cdd/6bd425e1-7427-4fe8-b1a7-80fff56102f7.png">
    <meta name="twitter:label1" content="Written by">
    <meta name="twitter:data1" content="Balajee Asish Brahmandam">
    <meta name="twitter:label2" content="Filed under">
    <meta name="twitter:data2" content="AI, Docker, Python, ollama, Open Source, handbook">
    <meta name="twitter:site" content="@freecodecamp">
    

    <meta property="og:image:width" content="1920">
    <meta property="og:image:height" content="1080">


        
    <script type="application/ld+json">{
	"@context": "https://schema.org",
	"@type": "Article",
	"publisher": {
		"@type": "Organization",
		"name": "freeCodeCamp.org",
		"url": "https://www.freecodecamp.org/news/",
		"logo": {
			"@type": "ImageObject",
			"url": "https://cdn.freecodecamp.org/platform/universal/fcc_primary.svg",
			"width": 2100,
			"height": 240
		}
	},
	"image": {
		"@type": "ImageObject",
		"url": "https://cloudmate-test.s3.us-east-1.amazonaws.com/uploads/covers/5fc16e412cae9c5b190b6cdd/6bd425e1-7427-4fe8-b1a7-80fff56102f7.png",
		"width": 1920,
		"height": 1080
	},
	"url": "https://www.freecodecamp.org/news/build-and-deploy-multi-agent-ai-with-python-and-docker/",
	"mainEntityOfPage": {
		"@type": "WebPage",
		"@id": "https://www.freecodecamp.org/news/"
	},
	"datePublished": "2026-02-23T15:55:01.909Z",
	"dateModified": "2026-02-25T20:33:46.470Z",
	"keywords": "AI, Docker, Python, ollama, Open Source, handbook",
	"description": "You wake up and open your laptop. Your browser has 27 tabs open, your inbox is overflowing with unread newsletters, and meeting notes are scattered across three apps. Sound familiar?\nNow imagine you h",
	"headline": "How to Build and Deploy a Multi-Agent AI System with Python and Docker",
	"author": {
		"@type": "Person",
		"name": "Balajee Asish Brahmandam",
		"url": "https://www.freecodecamp.org/news/author/Balajeeasish/",
		"sameAs": [],
		"image": {
			"@type": "ImageObject",
			"url": "https://cdn.hashnode.com/res/hashnode/image/upload/v1748785611098/171b728f-5b91-434d-8f3a-1e991f0a507f.jpeg?w=500&h=500&fit=crop&crop=entropy&auto=compress,format&format=webp",
			"width": 768,
			"height": 1024
		}
	}
}</script>


        <meta name="generator" content="Eleventy">
        <link rel="alternate" type="application/rss+xml" title="freeCodeCamp.org" href="https://www.freecodecamp.org/news/rss/">

        
        

        
  <meta name="x-fcc-source" data-test-label="x-fcc-source" content="Hashnode">

    </head>

    
        <body class="home-template">
    

    
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-5D6RKKP" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

    

        <div class="site-wrapper">
            <nav class="site-nav nav-padding universal-nav">
    <div class="site-nav-left">
        <div id="nav-left-search-container" class="fcc-search-container" data-test-label="fcc-search-container"></div>
    </div>
    <div class="site-nav-middle">
        <a class="site-nav-logo" href="https://www.freecodecamp.org/news/" data-test-label="site-nav-logo"><img src="https://cdn.freecodecamp.org/platform/universal/fcc_primary.svg" alt="freeCodeCamp.org"></a>
    </div>
    <div class="site-nav-right">
        <div class="nav-group">
            <button aria-expanded="false" class="exposed-button-nav" id="toggle-button-nav" data-test-label="header-menu-button">
              <span class="sr-only">Menu</span>
              <span class="menu-btn-text">Menu</span>
            </button>
            <ul id="menu-dropdown" class="nav-list" aria-labelledby="toggle-button-nav" data-test-label="header-menu">
                <li>
                    <div id="nav-right-search-container" class="fcc-search-container" data-test-label="fcc-search-container"></div>
                </li>
                <li><a class="nav-link nav-link-flex" id="nav-forum" rel="noopener noreferrer" href="https://forum.freecodecamp.org/" target="_blank" data-test-label="forum-button">Forum</a></li>
              <li><a class="nav-link nav-link-flex" id="nav-learn" rel="noopener noreferrer" href="https://www.freecodecamp.org/learn" target="_blank" data-test-label="learn-button">Curriculum</a></li>
            </ul>
            <a class="toggle-button-nav" id="nav-donate" rel="noopener noreferrer" href="https://www.freecodecamp.org/donate/" target="_blank" data-test-label="donate-button">Donate</a>
        </div>

    </div>
</nav>


            
            <a class="banner" id="banner" data-test-label="banner" rel="noopener noreferrer" target="_blank">
    <p id="banner-text"></p>
</a>


    
    <script>document.addEventListener("DOMContentLoaded",()=>{const e=document.getElementById("banner"),t=document.getElementById("banner-text");if(isAuthenticated){t.innerHTML=isDonor?"Thank you for supporting freeCodeCamp through <span>your donations</span>.":"Support our charity and our mission. <span>Donate to freeCodeCamp.org</span>.",e.href=isDonor?"https://www.freecodecamp.org/news/how-to-donate-to-free-code-camp/":"https://www.freecodecamp.org/donate";const o=isDonor?"donor":"authenticated";e.setAttribute("text-variation",o)}else t.innerHTML="Learn to code — <span>free 3,000-hour curriculum</span>",e.href="https://www.freecodecamp.org/",e.setAttribute("text-variation","default")});</script>


            <div id="error-message"></div>

            
    <main id="site-main" class="post-template site-main outer">
        <div class="inner ad-layout">
            <article class="post-full post">
                <header class="post-full-header">
                    <section class="post-full-meta">
                        <time class="post-full-meta-date" data-test-label="post-full-meta-date" datetime="2026-02-23T15:55:01.909Z">
                            February 23, 2026
                        </time>
                        
                            <span class="date-divider">/</span>
                            <a dir="ltr" href="/news/tag/ai/">
                                #AI
                            </a>
                        
                    </section>
                    <h1 class="post-full-title" data-test-label="post-full-title">How to Build and Deploy a Multi-Agent AI System with Python and Docker</h1>
                </header>
                
                    <div class="post-full-author-header" data-test-label="author-header-no-bio">
                        
                            
    
    
    

    <section class="author-card" data-test-label="author-card">
        
            
    <img srcset="https://cdn.hashnode.com/res/hashnode/image/upload/v1748785611098/171b728f-5b91-434d-8f3a-1e991f0a507f.jpeg?w=500&h=500&fit=crop&crop=entropy&auto=compress,format&format=webp 60w" sizes="60px" src="https://cdn.hashnode.com/res/hashnode/image/upload/v1748785611098/171b728f-5b91-434d-8f3a-1e991f0a507f.jpeg?w=500&h=500&fit=crop&crop=entropy&auto=compress,format&format=webp" class="author-profile-image" alt="Balajee Asish Brahmandam" width="768" height="1024" onerror="this.style.display='none'" data-test-label="profile-image">
  
        

        <section class="author-card-content author-card-content-no-bio">
            <span class="author-card-name">
                <a href="/news/author/Balajeeasish/" data-test-label="profile-link">
                    
                        Balajee Asish Brahmandam
                    
                </a>
            </span>
            
        </section>
    </section>

                        
                    </div>
                
                <figure class="post-full-image">
                    
    <picture>
      <source media="(max-width: 700px)" sizes="1px" srcset="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7 1w">
      <source media="(min-width: 701px)" sizes="(max-width: 800px) 400px, (max-width: 1170px) 700px, 1400px" srcset="https://cloudmate-test.s3.us-east-1.amazonaws.com/uploads/covers/5fc16e412cae9c5b190b6cdd/6bd425e1-7427-4fe8-b1a7-80fff56102f7.png">
      <img onerror="this.style.display='none'" src="https://cloudmate-test.s3.us-east-1.amazonaws.com/uploads/covers/5fc16e412cae9c5b190b6cdd/6bd425e1-7427-4fe8-b1a7-80fff56102f7.png" alt="How to Build and Deploy a Multi-Agent AI System with Python and Docker" ,="" width="1920" height="1080" data-test-label="feature-image">
    </picture>
  
                </figure>
                <section class="post-full-content">
                    <div class="post-and-sidebar">
                        <section class="post-content " data-test-label="post-content">
                            
<p>You wake up and open your laptop. Your browser has 27 tabs open, your inbox is overflowing with unread newsletters, and meeting notes are scattered across three apps. Sound familiar?</p>
<p>Now imagine you had a team of specialized assistants that worked overnight — one to read your inputs, one to summarize the key facts, one to rank what matters most, and one to format everything into a clean daily brief waiting in your inbox.</p>
<p>That is exactly what this handbook walks you through building. You will create a multi-agent AI system where four Python-based agents each handle one job. You will containerize each agent with Docker so the whole thing runs reliably on any machine. And you will wire it all together with Docker Compose so you can launch the entire pipeline with a single command.</p>
<p>This handbook assumes you are comfortable reading Python code, but it does not assume you have used Docker before. If you have never written a Dockerfile or run a container, that is fine — the fundamentals are covered as we go.</p>
<p>By the end, you will have a working system that turns digital noise into an organized daily digest, and you will understand the patterns behind it well enough to adapt them to your own projects.</p>
<h2>Table of Contents</h2>
<ul>
<li><p><a href="#what-is-a-multi-agent-system-and-why-build-one">What is a Multi-Agent System (and Why Build One)?</a></p>
<ul>
<li><p><a href="#how-traditional-scripts-work">How Traditional Scripts Work</a></p>
</li>
<li><p><a href="#how-ai-agents-are-different">How AI Agents are Different</a></p>
</li>
<li><p><a href="#why-use-multiple-agents-instead-of-one">Why Use Multiple Agents Instead of One?</a></p>
</li>
</ul>
</li>
<li><p><a href="#what-is-docker-and-why-does-it-matter-here">What is Docker (and Why Does It Matter Here)?</a></p>
<ul>
<li><p><a href="#the-environment-problem">The Environment Problem</a></p>
</li>
<li><p><a href="#how-docker-solves-this">How Docker Solves This</a></p>
</li>
<li><p><a href="#how-docker-layers-work">How Docker Layers Work</a></p>
</li>
<li><p><a href="#docker-vs-no-docker">Docker vs. No Docker</a></p>
</li>
</ul>
</li>
<li><p><a href="#how-to-plan-the-architecture">How to Plan the Architecture</a></p>
</li>
<li><p><a href="#prerequisites-and-environment-setup">Prerequisites and Environment Setup</a></p>
<ul>
<li><p><a href="#how-to-install-python">How to Install Python</a></p>
</li>
<li><p><a href="#how-to-install-docker">How to Install Docker</a></p>
</li>
<li><p><a href="#how-to-verify-your-setup">How to Verify Your Setup</a></p>
</li>
<li><p><a href="#how-to-set-up-the-project-structure">How to Set Up the Project Structure</a></p>
</li>
</ul>
</li>
<li><p><a href="#how-to-build-each-agent-step-by-step">How to Build Each Agent Step by Step</a></p>
<ul>
<li><p><a href="#the-ingestor-agent">The Ingestor Agent</a></p>
</li>
<li><p><a href="#the-summarizer-agent">The Summarizer Agent</a></p>
</li>
<li><p><a href="#the-prioritizer-agent">The Prioritizer Agent</a></p>
</li>
<li><p><a href="#the-formatter-agent">The Formatter Agent</a></p>
</li>
</ul>
</li>
<li><p><a href="#how-to-handle-secrets-and-api-keys">How to Handle Secrets and API Keys</a></p>
<ul>
<li><p><a href="#using-env-files-for-development">Using .env Files for Development</a></p>
</li>
<li><p><a href="#how-to-use-docker-secrets-for-production">How to Use Docker Secrets for Production</a></p>
</li>
</ul>
</li>
<li><p><a href="#how-to-orchestrate-everything-with-docker-compose">How to Orchestrate Everything with Docker Compose</a></p>
</li>
<li><p><a href="#how-to-run-the-pipeline">How to Run the Pipeline</a></p>
</li>
<li><p><a href="#how-to-test-the-pipeline">How to Test the Pipeline</a></p>
<ul>
<li><p><a href="#unit-tests">Unit Tests</a></p>
</li>
<li><p><a href="#integration-tests">Integration Tests</a></p>
</li>
</ul>
</li>
<li><p><a href="#how-to-add-logging-and-observability">How to Add Logging and Observability</a></p>
</li>
<li><p><a href="#cost-rate-limits-and-graceful-degradation">Cost, Rate Limits, and Graceful Degradation</a></p>
</li>
<li><p><a href="#security-and-privacy-considerations">Security and Privacy Considerations</a></p>
</li>
<li><p><a href="#how-to-use-a-local-llm-for-full-privacy-ollama">How to Use a Local LLM for Full Privacy (Ollama)</a></p>
</li>
<li><p><a href="#example-seed-data-and-expected-output">Example Seed Data and Expected Output</a></p>
</li>
<li><p><a href="#how-to-automate-daily-execution">How to Automate Daily Execution</a></p>
</li>
<li><p><a href="#how-to-use-cron-on-linux-or-macos">How to Use Cron on Linux or macOS</a></p>
</li>
<li><p><a href="#how-to-use-task-scheduler-on-windows">How to Use Task Scheduler on Windows</a></p>
</li>
<li><p><a href="#how-to-add-delivery-notifications">How to Add Delivery Notifications</a></p>
</li>
<li><p><a href="#troubleshooting-common-errors">Troubleshooting Common Errors</a></p>
</li>
<li><p><a href="#production-deployment-options">Production Deployment Options</a></p>
<ul>
<li><p><a href="#docker-swarm">Docker Swarm</a></p>
</li>
<li><p><a href="#kubernetes">Kubernetes</a></p>
</li>
</ul>
</li>
<li><p><a href="#cloud-platforms">Cloud Platforms</a></p>
</li>
<li><p><a href="#conclusion-and-next-steps">Conclusion and Next Steps</a></p>
</li>
</ul>
<h2>What is a Multi-Agent System (and Why Build One)?</h2>
<h3>How Traditional Scripts Work</h3>
<p>A traditional Python script follows a fixed path. It reads some input, processes it through a series of hard-coded steps, and writes the output. If the input format changes even slightly, the script often breaks. Think of it like a train on a track. Trains are fast and efficient, but they can only go where the rails take them. If the track is blocked, the train stops.</p>
<h3>How AI Agents are Different</h3>
<p>An AI agent is more like a bus driver. It has a destination (a goal), but it can decide which route to take based on current conditions (the data). If one road is blocked, it finds another.</p>
<p>Agents typically follow a loop called the <strong>ReAct pattern</strong>, which stands for Reasoning plus Acting. At each step, the agent thinks about what to do, takes an action, observes the result, and decides whether it has reached its goal. If not, it loops back and tries again. If so, it finishes.</p>
<p>In practice, this means an LLM-based agent can handle messy, unpredictable input much better than a traditional script. If a newsletter changes its format, the summarizer agent can still extract the key points because it reasons about the content rather than parsing a rigid structure.</p>
<h3>Why Use Multiple Agents Instead of One?</h3>
<p>You might wonder: why not just use one powerful agent that does everything? That approach is called the "God Model" pattern, and it has real problems. When you ask a single LLM to ingest data, summarize it, prioritize it, and format it all in one prompt, you are giving it too much to think about at once. LLMs have a limited context window and limited attention. The more tasks you pile on, the more likely the model is to hallucinate, skip steps, or produce inconsistent output.</p>
<p>A multi-agent system solves this through <strong>separation of concerns</strong>. Each agent has one narrow job. The Ingestor reads and combines raw files, with no LLM needed. The Summarizer calls the LLM with a focused prompt: just summarize this text. The Prioritizer scores lines by keyword with no LLM needed. And the Formatter writes Markdown output, also with no LLM.</p>
<p>This design has several advantages. Each agent is simpler to build, test, and debug. You can swap out the Summarizer for a better model without touching anything else. And you can scale individual agents independently — for example, running multiple Summarizers in parallel if you have a lot of input.</p>
<h2>What is Docker (and Why Does It Matter Here)?</h2>
<h3>The Environment Problem</h3>
<p>If you have ever shared a Python project with someone and heard "it does not work on my machine," you already understand the problem Docker solves. Every Python project depends on specific versions of Python itself, plus libraries like <code>openai</code>, <code>requests</code>, or <code>beautifulsoup4</code>. These dependencies live in your operating system's environment. When you install a new library or upgrade Python, you might break a different project that depends on the old version.</p>
<p>Virtual environments help, but they only isolate Python packages. They do not isolate the operating system, system libraries, or other tools your code might need. And they do not guarantee that someone else can recreate your exact environment. For a multi-agent system, this problem gets worse. Each agent might need different dependencies. If they share an environment, their dependencies can conflict.</p>
<h3>How Docker Solves This</h3>
<p>Docker packages your code, its dependencies, and a minimal operating system into a single unit called a <strong>container</strong>. When you run that container, it behaves exactly the same way regardless of what machine it is running on — your laptop, a coworker's computer, or a cloud server. Think of a Docker container like a shipping container for software. The contents are sealed inside, protected from the outside environment.</p>
<p>There are a few key Docker concepts to understand:</p>
<p><strong>Image</strong> — A read-only template that contains your code, dependencies, and a minimal OS. You build an image from a Dockerfile. Think of it as a recipe.</p>
<p><strong>Container</strong> — A running instance of an image. When you "run" an image, Docker creates a container from it. Think of it as a dish made from the recipe.</p>
<p><strong>Dockerfile</strong> — A text file with instructions for building an image. It specifies the base OS, what to install, what code to copy in, and what command to run when the container starts.</p>
<p><strong>Volume</strong> — A way to share files between your computer and a container, or between multiple containers. Our agents will use a shared volume to pass data to each other.</p>
<p><strong>Docker Compose</strong> — A tool for defining and running multiple containers together. You describe all your containers in a single YAML file, and Compose handles building, networking, and ordering them.</p>
<h3>How Docker Layers Work</h3>
<p>Docker builds images in layers. Each instruction in a Dockerfile creates a new layer. Docker caches these layers, so if a layer has not changed since the last build, Docker reuses the cached version instead of rebuilding it. This is why Dockerfiles are structured in a specific order: the base OS layer rarely changes, the dependency installation layer changes when <code>requirements.txt</code> changes, and the application code layer changes on every code edit. By putting dependency installation before the code copy, Docker only re-runs <code>pip install</code> when your requirements actually change, making rebuilds much faster — seconds instead of minutes.</p>
<h3>Docker vs. No Docker</h3>
<p>To be clear, you do not strictly need Docker for this tutorial. You can run all four agents as plain Python scripts. But without Docker you face dependency conflicts from a shared environment, manual process management for scaling, having to redo all setup on every new machine, complex orchestration for testing, and painful Python version management when one agent needs 3.8 and another needs 3.10. With Docker, each agent has its own isolated environment, you run multiple containers in parallel with one command, <code>docker compose up</code> produces identical results everywhere, and each container runs its own Python version independently.</p>
<p>For a personal project, either approach works. But if you ever want to share this system, deploy it to a server, or run it in the cloud, Docker makes the difference between "here is a README with 15 setup steps" and "run <code>docker compose up</code>."</p>
<h2>How to Plan the Architecture</h2>
<p>Before writing any code, it is worth mapping out how the pieces fit together. The full system consists of four agents arranged in a sequential pipeline, all orchestrated by Docker Compose. Data flows through the Ingestor Agent, the Summarizer Agent, the Prioritizer Agent, and the Formatter Agent in that order. Each agent reads from a shared volume, processes its input, writes the result, and exits. Docker Compose enforces execution order by waiting for each container to finish successfully before starting the next one.</p>
<p>This is a synchronous pipeline: agents run one at a time, in sequence. It is the simplest multi-agent pattern to implement and understand. For more complex systems, you could replace the shared volume with a message broker like Redis or RabbitMQ, which lets agents run asynchronously and react to events. But for this daily-digest use case, the sequential approach is exactly right.</p>
<p>In terms of responsibilities:</p>
<ul>
<li><p><strong>Ingestor</strong> — Reads and combines raw files from <code>/data/input/</code> into <code>ingested.txt</code>. No LLM required.</p>
</li>
<li><p><strong>Summarizer</strong> — Distills key points from <code>ingested.txt</code> into <code>summary.txt</code>. The only agent that requires an LLM.</p>
</li>
<li><p><strong>Prioritizer</strong> — Scores items by urgency keywords, turning <code>summary.txt</code> into <code>prioritized.txt</code>. No LLM.</p>
</li>
<li><p><strong>Formatter</strong> — Produces the final Markdown report, <code>daily_digest.md</code>. No LLM.</p>
</li>
</ul>
<p>Notice that only one of the four agents actually calls an LLM. The others are plain Python. This is intentional — you should only use an LLM when you need reasoning or language understanding. Everything else should be deterministic code. It is cheaper, faster, and more predictable.</p>
<h2>Prerequisites and Environment Setup</h2>
<p>You need the following tools installed before starting:</p>
<ul>
<li><p><strong>Python</strong> 3.10 or higher — the language for the agents</p>
</li>
<li><p><strong>Docker Desktop</strong> (Engine 20.10+) — the container runtime</p>
</li>
<li><p><strong>Docker Compose</strong> v2 (included with Docker Desktop) — multi-container orchestration</p>
</li>
<li><p><strong>Git</strong> 2.30+ — version control</p>
</li>
<li><p><strong>OpenAI Python SDK</strong> (<code>openai &gt;= 1.0</code>) — LLM API access</p>
</li>
<li><p><strong>Redis or RabbitMQ</strong> (optional) — async message queuing</p>
</li>
<li><p><strong>PostgreSQL</strong> (optional) — persistent data storage</p>
</li>
</ul>
<h3>How to Install Python</h3>
<p>Download Python from <a href="https://python.org/">python.org</a>. On Windows, check the "Add Python to PATH" box during installation. On macOS, you can use Homebrew:</p>
<pre><code class="language-bash">brew install python@3.12
</code></pre>
<p>On Linux (Ubuntu/Debian), use your package manager:</p>
<pre><code class="language-bash">sudo apt update &amp;&amp; sudo apt install python3 python3-pip
</code></pre>
<h3>How to Install Docker</h3>
<p>Docker Desktop is the easiest way to get started on Windows and macOS. Download it from <a href="https://docker.com/">docker.com</a> and follow the prompts. On Windows, Docker Desktop requires WSL2 — the installer will guide you through enabling it. On Linux, install Docker Engine directly:</p>
<pre><code class="language-bash"># Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER  # So you don't need sudo for docker commands
</code></pre>
<p>After installing, log out and back in for the group change to take effect.</p>
<h3>How to Verify Your Setup</h3>
<p>Open your terminal and run these commands. Each should print a version number without errors:</p>
<pre><code class="language-bash">python --version        # Should show 3.10 or higher
docker --version        # Should show 20.10 or higher
docker compose version  # Should show v2.x
git --version           # Should show 2.30 or higher
</code></pre>
<p>If any command fails, go back to the installation step for that tool. The most common issue is that the command is not in your PATH.</p>
<h2>How to Set Up the Project Structure</h2>
<p>Each agent lives in its own directory with its own code, Dockerfile, and requirements file. This isolation means you can build, test, and update each agent independently. Create the following structure:</p>
<pre><code class="language-plaintext">multi-agent-digest/
├── agents/
│   ├── ingestor/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── summarizer/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── prioritizer/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── formatter/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
├── data/
│   └── input/          # Your raw files go here
├── output/              # The final digest appears here
├── tests/               # Unit and integration tests
├── .env                 # API keys (gitignored!)
├── .gitignore
├── docker-compose.yml
└── README.md
</code></pre>
<p>You can create the folders quickly from the terminal:</p>
<pre><code class="language-bash">mkdir -p multi-agent-digest/agents/{ingestor,summarizer,prioritizer,formatter}
mkdir -p multi-agent-digest/{data/input,output,tests}
cd multi-agent-digest
</code></pre>
<h2>How to Build Each Agent Step by Step</h2>
<p>Every agent follows the same simple pattern: read an input file from the shared volume, do its job, and write an output file. This consistency makes the system easy to understand and extend.</p>
<h3>The Ingestor Agent</h3>
<p>The Ingestor is the entry point of the pipeline. Its job is to read all text files from the input folder and combine them into a single file that the Summarizer can process. This is the simplest agent — no external libraries, no API calls, just file reading and writing.</p>
<p><code>agents/ingestor/app.py</code></p>
<pre><code class="language-python">import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ingestor")

INPUT_DIR = "/data/input"
OUTPUT_FILE = "/data/ingested.txt"

def ingest():
    content = ""
    files_processed = 0
    for filename in sorted(os.listdir(INPUT_DIR)):
        filepath = os.path.join(INPUT_DIR, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content += f"\n--- {filename} ---\n"
                    content += f.read()
                    content += "\n"
                    files_processed += 1
            except Exception as e:
                logger.error(f"Failed to read {filename}: {e}")

    if files_processed == 0:
        logger.warning("No input files found in /data/input/")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(content)
    logger.info(f"Ingested {files_processed} files -&gt; {OUTPUT_FILE}")

if __name__ == "__main__":
    ingest()
</code></pre>
<p>The <code>logging.basicConfig</code> block sets up structured logging. Every agent uses the same log format, so when Docker Compose runs them together, you get a clean, consistent timeline. The <code>sorted(os.listdir())</code> call ensures files are processed in alphabetical order — without it, the order depends on the filesystem and can vary between machines. The <code>try/except</code> block around each file read means a single corrupted file will not crash the entire pipeline. And if no files are found at all, the agent writes an empty output file rather than crashing, so downstream agents can handle empty input gracefully.</p>
<p><code>agents/ingestor/Dockerfile</code></p>
<pre><code class="language-dockerfile">FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
</code></pre>
<p><code>FROM python:3.10-slim</code> starts with a minimal Linux image that has Python pre-installed. The <code>-slim</code> variant is about 120 MB versus 900 MB for the full image. <code>WORKDIR /app</code> sets the working directory inside the container. <code>COPY requirements.txt</code> and <code>RUN pip install</code> handle dependencies at build time, not runtime. <code>COPY app.py</code> copies the application code last because it changes most often, and Docker caches previous layers. <code>CMD</code> specifies the command to run when the container starts.</p>
<p>Since the Ingestor uses only standard library modules, its <code>requirements.txt</code> can be empty:</p>
<pre><code class="language-plaintext"># No external dependencies needed
</code></pre>
<h3>The Summarizer Agent</h3>
<p>The Summarizer is the most complex agent in the pipeline. It reads the ingested text and calls an LLM API to produce a concise summary. This is the only agent that makes a network call, which means it is the only one that can fail due to external factors: the API might be down, you might hit rate limits, or your key might be invalid.</p>
<p><code>agents/summarizer/app.py</code>:</p>
<pre><code class="language-python">import os
import logging
import time
from openai import OpenAI, RateLimitError, APIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("summarizer")

INPUT_FILE = "/data/ingested.txt"
OUTPUT_FILE = "/data/summary.txt"

client = OpenAI()  # reads OPENAI_API_KEY from environment

SYSTEM_PROMPT = (
    "You are a helpful assistant that summarizes long text "
    "into key bullet points. Each bullet should be one "
    "concise sentence capturing a core insight."
)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def summarize(text, retries=MAX_RETRIES):
    """Call the LLM API with retry logic for rate limits."""
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text[:8000]}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except RateLimitError:
            wait = RETRY_DELAY * (attempt + 1)
            logger.warning(f"Rate limited. Retrying in {wait}s...")
            time.sleep(wait)
        except APIError as e:
            logger.error(f"API error: {e}")
            raise
    raise RuntimeError("Max retries exceeded for LLM API call")

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    if not raw_text.strip():
        logger.warning("Empty input. Writing fallback summary.")
        summary = "No content to summarize."
    else:
        try:
            summary = summarize(raw_text)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            summary = f"Summarization failed: {e}"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(summary)
    logger.info(f"Summary written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
</code></pre>
<p>The <code>OpenAI()</code> client automatically reads the <code>OPENAI_API_KEY</code> environment variable — you do not need to pass the key explicitly in code, which is both cleaner and safer. The <code>text[:8000]</code> slice limits how much text is sent to the API. Sending fewer tokens means faster responses and lower cost. For production, you would want smarter chunking that splits on sentence or paragraph boundaries rather than a raw character count.</p>
<p><strong>Temperature 0.3</strong> makes the output more focused and deterministic, which is ideal for summarization. The retry logic catches <code>RateLimitError</code> specifically and waits longer each time (5, 10, then 15 seconds) — this is called <strong>exponential backoff</strong>. Other API errors raise immediately because retrying them will not help. If the input is empty or the API fails completely, the agent writes a fallback message instead of crashing, so the downstream agents can still run.</p>
<p><code>agents/summarizer/requirements.txt</code>:</p>
<pre><code class="language-plaintext">openai&gt;=1.0
</code></pre>
<p>The Dockerfile is identical to the Ingestor's.</p>
<h3>The Prioritizer Agent</h3>
<p>The Prioritizer takes the LLM-generated summary and scores each line based on urgency keywords. This is a rule-based agent — no LLM call needed. It is fast, deterministic, and free.</p>
<p><code>agents/prioritizer/app.py</code>:</p>
<pre><code class="language-python">import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("prioritizer")

INPUT_FILE = "/data/summary.txt"
OUTPUT_FILE = "/data/prioritized.txt"

PRIORITY_KEYWORDS = [
    "urgent", "today", "asap", "important",
    "deadline", "critical", "action required"
]

def score_line(line):
    """Count how many priority keywords appear in a line."""
    lower = line.lower()
    return sum(1 for kw in PRIORITY_KEYWORDS if kw in lower)

def prioritize():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    scored = [(line, score_line(line)) for line in lines]
    scored.sort(key=lambda x: x[1], reverse=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for line, score in scored:
            out.write(f"[{score}] {line}\n")

    logger.info(f"Prioritized {len(scored)} items -&gt; {OUTPUT_FILE}")

if __name__ == "__main__":
    prioritize()
</code></pre>
<p>The scoring function counts how many priority keywords appear in each line. A line containing "urgent deadline" scores 2, and a line with no keywords scores 0. The scored lines are sorted in descending order, so the most urgent items appear first. Each line is prefixed with its score in brackets, like <code>[2] Urgent: quarterly report due today</code>. In a more advanced system, you could replace this keyword scorer with an LLM-based ranker, but for a daily digest, simple keyword matching works surprisingly well.</p>
<p>This agent has no pip dependencies, so the Dockerfile skips the requirements step:</p>
<p><code>agents/prioritizer/Dockerfile</code>:</p>
<pre><code class="language-dockerfile">FROM python:3.10-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
</code></pre>
<h3>The Formatter Agent</h3>
<p>The Formatter is the final agent in the pipeline. It reads the scored lines and writes a clean Markdown document to the output directory.</p>
<p><code>agents/formatter/app.py</code>:</p>
<pre><code class="language-python">import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("formatter")

INPUT_FILE = "/data/prioritized.txt"
OUTPUT_FILE = "/output/daily_digest.md"

def format_to_markdown():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    today = datetime.now().strftime('%Y-%m-%d')

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("# Your Daily AI Digest\n\n")
        out.write(f"**Date:** {today}\n\n")
        out.write("## Top Insights\n\n")
        for line in lines:
            if '] ' in line:
                score = line.split(']')[0][1:]
                content = line.split('] ', 1)[1]
                out.write(f"- **Priority {score}**: {content}\n")
            else:
                out.write(f"- {line}\n")

    logger.info(f"Digest written to {OUTPUT_FILE}")

if __name__ == "__main__":
    format_to_markdown()
</code></pre>
<p>Notice that the Formatter writes to <code>/output</code> instead of <code>/data</code>. This is a separate volume mount in Docker Compose. The <code>/data</code> volume is internal plumbing that agents use to communicate, while the <code>/output</code> volume maps to a folder on your host machine where you can access the final result. The <code>split('] ', 1)</code> with <code>maxsplit=1</code> ensures that bracket characters inside the actual content do not break the parsing.</p>
<p>The Dockerfile is the same as the Prioritizer's (no external dependencies).</p>
<h2>How to Handle Secrets and API Keys</h2>
<blockquote>
<p>⚠️ <strong>Warning:</strong> Never commit API keys or secrets to version control. A leaked OpenAI key can rack up thousands of dollars in charges before you notice.</p>
</blockquote>
<h3>Using .env Files for Development</h3>
<p>Create a <code>.env</code> file in your project root:</p>
<pre><code class="language-plaintext"># .env -- DO NOT COMMIT THIS FILE
OPENAI_API_KEY=sk-your-key-here
</code></pre>
<p>Then immediately add it to your <code>.gitignore</code>:</p>
<pre><code class="language-plaintext"># .gitignore
.env
output/
data/ingested.txt
data/summary.txt
data/prioritized.txt
__pycache__/
*.pyc
</code></pre>
<p>Docker Compose reads <code>.env</code> files automatically when it starts. In your <code>docker-compose.yml</code>, you reference the variable with <code>${OPENAI_API_KEY}</code>, and Compose substitutes the real value at runtime. The key never appears in your Dockerfile, your code, or your version history.</p>
<h3>How to Use Docker Secrets for Production</h3>
<p>For production deployments on Docker Swarm or Kubernetes, environment variables are visible in process listings and inspect commands. Docker secrets are more secure:</p>
<pre><code class="language-bash"># Create the secret
echo "sk-your-key-here" | docker secret create openai_key -
</code></pre>
<pre><code class="language-yaml"># Reference in docker-compose.yml (Swarm mode only)
services:
  summarizer:
    secrets:
      - openai_key

secrets:
  openai_key:
    external: true
</code></pre>
<p>The secret gets mounted as a read-only file at <code>/run/secrets/openai_key</code> inside the container. Your code reads the key from that file instead of from an environment variable.</p>
<h2>How to Orchestrate Everything with Docker Compose</h2>
<p>With all four agents built, Docker Compose ties them together. It builds each container, mounts the shared volumes, passes environment variables, and enforces the correct execution order.</p>
<p><code>docker-compose.yml</code>:</p>
<pre><code class="language-yaml">version: "3.9"

services:
  ingestor:
    build: ./agents/ingestor
    container_name: agent_ingestor
    volumes:
      - ./data:/data
    restart: "no"

  summarizer:
    build: ./agents/summarizer
    container_name: agent_summarizer
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      ingestor:
        condition: service_completed_successfully
    volumes:
      - ./data:/data
    deploy:
      resources:
        limits:
          memory: 512M
    restart: "no"

  prioritizer:
    build: ./agents/prioritizer
    container_name: agent_prioritizer
    depends_on:
      summarizer:
        condition: service_completed_successfully
    volumes:
      - ./data:/data
    restart: "no"

  formatter:
    build: ./agents/formatter
    container_name: agent_formatter
    depends_on:
      prioritizer:
        condition: service_completed_successfully
    volumes:
      - ./data:/data
      - ./output:/output
    restart: "no"
</code></pre>
<p>The <code>depends_on</code> with <code>condition: service_completed_successfully</code> is the key to the sequential pipeline. This setting (available in Compose v2) tells Docker to wait until the previous container exits with a zero exit code before starting the next one. Without this condition, <code>depends_on</code> only waits for the container to <em>start</em>, not to <em>finish</em> — which would cause race conditions where the Summarizer tries to read a file the Ingestor has not written yet.</p>
<p>The <strong>volume mounts</strong> (<code>./data:/data</code>) map your local data folder into each container. All agents share this volume, which is how they pass files to each other. The Formatter also gets <code>./output:/output</code> so the final digest lands on your host machine. The <strong>memory limit</strong> of 512M on the Summarizer prevents it from consuming too much RAM. And <code>restart: "no"</code> ensures Docker does not restart the agents after they finish, since they are batch jobs.</p>
<h3>How to Run the Pipeline</h3>
<pre><code class="language-bash">docker compose up --build
</code></pre>
<p>The <code>--build</code> flag tells Compose to rebuild the images before running. You will see structured logs from each agent in sequence:</p>
<pre><code class="language-plaintext">agent_ingestor    | 2025-01-20 07:00:01 [INFO] ingestor: Ingested 3 files
agent_summarizer  | 2025-01-20 07:00:04 [INFO] summarizer: Summary written
agent_prioritizer | 2025-01-20 07:00:05 [INFO] prioritizer: Prioritized 8 items
agent_formatter   | 2025-01-20 07:00:05 [INFO] formatter: Digest written
</code></pre>
<p>When all four containers finish, open <code>output/daily_digest.md</code> to see your morning brief.</p>
<h2>How to Test the Pipeline</h2>
<h3>Unit Tests</h3>
<p>Because each agent's core logic is a plain Python function, you can test it in isolation without Docker.</p>
<p><code>tests/test_prioritizer.py</code></p>
<pre><code class="language-python">import sys
sys.path.insert(0, 'agents/prioritizer')
from app import score_line

def test_urgent_keyword_scores_one():
    assert score_line("This is urgent") == 1

def test_multiple_keywords_stack():
    assert score_line("Urgent and important deadline") == 3

def test_no_keywords_scores_zero():
    assert score_line("Regular project update") == 0

def test_scoring_is_case_insensitive():
    assert score_line("URGENT DEADLINE ASAP") == 3
</code></pre>
<p>Run the tests with pytest:</p>
<pre><code class="language-bash">pip install pytest
python -m pytest tests/ -v
</code></pre>
<p>Writing tests for each agent's core function means you can catch bugs before you build any Docker images, saving a lot of time compared to debugging inside running containers.</p>
<h3>Integration Tests</h3>
<p>To test the full pipeline end-to-end, create known input files and verify the expected output:</p>
<pre><code class="language-bash"># Create test data
mkdir -p data/input
echo "Urgent: quarterly report due today" &gt; data/input/test.txt
echo "Regular standup notes, no blockers" &gt;&gt; data/input/test.txt

# Run the pipeline
docker compose up --build

# Verify the output exists and contains expected content
test -f output/daily_digest.md &amp;&amp; echo "File exists: PASS" || echo "File missing: FAIL"
grep -q "Priority" output/daily_digest.md &amp;&amp; echo "Content check: PASS" || echo "Content check: FAIL"
</code></pre>
<h2>How to Add Logging and Observability</h2>
<p>Every agent uses Python's <code>logging</code> module with a consistent format. When Docker Compose runs all four containers, it interleaves their logs with container name prefixes, giving you a unified timeline of the entire pipeline.</p>
<p>For production systems, consider switching to JSON-formatted logs. They are easier to parse with log aggregation tools like the ELK Stack, Grafana Loki, or AWS CloudWatch:</p>
<pre><code class="language-python">import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "agent": record.name,
            "message": record.getMessage(),
        })
</code></pre>
<p>To use this formatter, replace the <code>basicConfig</code> call with a handler:</p>
<pre><code class="language-python">handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("summarizer")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
</code></pre>
<p>The most useful metrics to track include the number of files ingested per run, Summarizer latency (time from API call to response), LLM token usage for cost tracking, the number of errors and retries per agent, and whether <code>daily_digest.md</code> was successfully generated. A simple approach for personal use is to write a JSON metrics file alongside the digest in the output directory. For team or production use, consider adding Prometheus metrics or sending data to a monitoring service.</p>
<h2>Cost, Rate Limits, and Graceful Degradation</h2>
<p>The Summarizer is the only agent that calls a paid API. Here is what you can expect to pay:</p>
<table style="min-width:100px"><colgroup><col style="min-width:25px"><col style="min-width:25px"><col style="min-width:25px"><col style="min-width:25px"></colgroup><tbody><tr><th><p>Model</p></th><th><p>Input Cost</p></th><th><p>Output Cost</p></th><th><p>Cost per Daily Run</p></th></tr><tr><td><p><code>gpt-4o-mini</code></p></td><td><p>\(0.15 / 1M tokens</p></td><td><p>\)0.60 / 1M tokens</p></td><td><p>Less than \(0.01</p></td></tr><tr><td><p><code>gpt-4o</code></p></td><td><p>\)2.50 / 1M tokens</p></td><td><p>\(10.00 / 1M tokens</p></td><td><p>\)0.02 to \(0.10</p></td></tr><tr><td><p>Local model (Ollama)</p></td><td><p>Free (uses your hardware)</p></td><td><p>Free</p></td><td><p>\)0.00</p></td></tr></tbody></table>

<p>For a daily personal digest processing a few thousand tokens of input, <code>gpt-4o-mini</code> costs less than a penny per run. That works out to roughly three dollars per year.</p>
<p>To protect against unexpected bills, set a monthly spending cap in your OpenAI dashboard. You can also set per-minute rate limits to prevent runaway usage if a bug causes repeated API calls.</p>
<p>Beyond the retry logic already built into the Summarizer, you can cache LLM responses so that if the same input text appears again you reuse the previous summary instead of calling the API. Use the cheapest model that gives acceptable results — for summarization, <code>gpt-4o-mini</code> usually works as well as <code>gpt-4o</code> at a fraction of the cost. And batch requests when possible by combining many small texts into one API call.</p>
<p>The Summarizer already writes a fallback message when the API fails. This is the most important form of graceful degradation: the pipeline keeps running, and you get a less useful digest instead of nothing at all. If the digest is critical for your workflow, add an alerting step — for example, you could extend the Formatter to send a Slack notification when the Summarizer falls back.</p>
<h2>Security and Privacy Considerations</h2>
<p>When you feed personal data emails, meeting notes, private newsletters into an LLM, you need to think carefully about where that data goes.</p>
<p>Text you send to OpenAI or similar providers leaves your machine and is processed on their servers. As of early 2025, OpenAI's API does not use submitted data for model training by default, but policies can change. Always check your provider's current data retention and usage policies. If your input contains personally identifiable information like names, email addresses, or phone numbers, consider stripping it before calling the API, or use a local model.</p>
<p>The intermediate files created during the pipeline (<code>ingested.txt</code>, <code>summary.txt</code>, <code>prioritized.txt</code>) contain processed versions of your raw input. For personal use, keep them for debugging and delete manually. For automated pipelines, add a cleanup step that deletes intermediate files after the digest is generated. If you operate in the EU, review GDPR requirements around data minimization, right to deletion, and records of processing.</p>
<p>To secure your containers, use minimal base images like <code>python:3.10-slim</code> to reduce the attack surface, run containers as a non-root user by adding a <code>USER</code> directive to your Dockerfiles, update base images regularly (at least monthly) to pick up security patches, and scan your images for vulnerabilities using <code>docker scout</code> or Trivy.</p>
<h2>How to Use a Local LLM for Full Privacy (Ollama)</h2>
<p>If you want to keep all data on your machine and avoid sending anything to external APIs, you can swap the OpenAI API for a local model running through <strong>Ollama</strong>. Ollama lets you run open-source LLMs locally, handling model weight downloads, memory management, and serving an API.</p>
<p>To set up Ollama:</p>
<pre><code class="language-bash"># Install Ollama (macOS or Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (llama3 is a good general-purpose choice)
ollama pull llama3

# Verify it is running
ollama list
</code></pre>
<p>Replace the OpenAI API call in the Summarizer with a request to Ollama's local API:</p>
<pre><code class="language-python">import requests

def summarize_locally(text):
    """Call a local Ollama instance from inside a Docker container."""
    url = "http://host.docker.internal:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": (
            "Summarize the following text into key "
            f"bullet points:\n\n{text}"
        ),
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get('response', 'No response')
    except requests.exceptions.RequestException as e:
        return f"Ollama error: {e}"
</code></pre>
<p>The <code>host.docker.internal</code> hostname lets a container communicate with services running on the host machine. Ollama runs on your host (not inside a container), so this is how the Summarizer reaches it.</p>
<blockquote>
<p><strong>Note:</strong> On Linux, <code>host.docker.internal</code> may not resolve by default. Add this to your <code>docker-compose.yml</code> under the summarizer service: <code>extra_hosts: ["host.docker.internal:host-gateway"]</code></p>
</blockquote>
<p>Local models are slower than cloud APIs and require decent hardware (at least 8 GB of RAM for smaller models, 16 GB or more for larger ones). But they are free, fully private, and work without an internet connection.</p>
<h2>Example Seed Data and Expected Output</h2>
<p>To test the full pipeline without real newsletters, create these sample input files:</p>
<p><code>data/input/newsletter_ai.txt</code></p>
<pre><code class="language-plaintext">AI Weekly Roundup - January 2025
OpenAI released a new reasoning model this week.
URGENT: New EU AI Act regulations take effect in March.
Google announced updates to their Gemini model family.
A startup raised $50M for AI-powered code review tools.
</code></pre>
<p><code>data/input/meeting_notes.txt</code>:</p>
<pre><code class="language-plaintext">Team Standup Notes - Monday
IMPORTANT: Deadline for Q1 report is this Friday.
Action required: Review the updated API documentation.
Sprint velocity is on track. No blockers reported.
</code></pre>
<p>Expected output in <code>output/daily_digest.md</code>:</p>
<pre><code class="language-markdown"># Your Daily AI Digest

**Date:** 2025-01-20

## Top Insights

- **Priority 3**: IMPORTANT: Deadline for Q1 report due Friday
- **Priority 2**: URGENT: New EU AI Act regulations in March
- **Priority 1**: Action required: Review the updated API docs
- **Priority 0**: OpenAI released a new reasoning model
- **Priority 0**: Sprint velocity is on track
</code></pre>
<p>The exact summary text will vary depending on your LLM model and settings, but the structure and priority ordering should remain consistent.</p>
<h2>How to Automate Daily Execution</h2>
<p>Now that the pipeline works end-to-end with a single command, you can schedule it to run automatically every morning.</p>
<h3>How to Use Cron on Linux or macOS</h3>
<p>Open your crontab with <code>crontab -e</code> and add this line to run the pipeline every day at 7:00 AM:</p>
<pre><code class="language-bash">0 7 * * * cd /path/to/multi-agent-digest &amp;&amp; docker compose up --build &gt;&gt; cron.log 2&gt;&amp;1
</code></pre>
<p>The <code>&gt;&gt; cron.log 2&gt;&amp;1</code> part redirects all output (including errors) to a log file so you can check it later. Make sure your machine is running at the scheduled time and Docker Desktop is started.</p>
<h3>How to Use Task Scheduler on Windows</h3>
<p>Open Task Scheduler and create a new task. Under "Actions," set the program to:</p>
<pre><code class="language-bash">wsl -e bash -c 'cd /mnt/c/path/to/multi-agent-digest &amp;&amp; docker compose up --build'
</code></pre>
<p>Set the trigger to fire every morning at your preferred time.</p>
<h3>How to Add Delivery Notifications</h3>
<p>For the digest to be truly useful, you want it delivered to you rather than sitting in a folder. Here are three options:</p>
<p><strong>Email</strong> — Extend the Formatter to send the digest via Python's <code>smtplib</code> module. You will need SMTP credentials for a service like Gmail, SendGrid, or Amazon SES.</p>
<p><strong>Slack</strong> — Create an incoming webhook in your Slack workspace and POST the digest as a message. This takes about 10 lines of code.</p>
<p><strong>Notion or Obsidian</strong> — Use their APIs to create a new page or note with the digest content each morning.</p>
<h2>Troubleshooting Common Errors</h2>
<p><strong>Container exits with OOM error</strong> — Large files or LLM processing are exceeding memory. Increase the memory limit in <code>docker-compose.yml</code> under <code>deploy &gt; resources &gt; limits &gt; memory</code>. Try <code>1G</code>.</p>
<p><strong>Rate limit errors from OpenAI</strong> — The retry logic handles temporary rate limits automatically. Check your OpenAI dashboard for usage caps.</p>
<p><code>depends_on</code> <strong>does not wait for completion</strong> — Make sure you are using <code>condition: service_completed_successfully</code>, which requires Docker Compose v2.</p>
<p><strong>Permission denied on</strong> <code>/output</code> — Volume mount permissions mismatch. Run <code>chmod -R 777 ./output</code> on the host, or add a <code>USER</code> directive to your Dockerfiles.</p>
<p><code>OPENAI_API_KEY</code> <strong>not found</strong> — The <code>.env</code> file may be missing or not in the right directory. Create <code>.env</code> in the same folder as <code>docker-compose.yml</code> and verify with <code>docker compose config</code>.</p>
<p><strong>Cannot reach Ollama from container</strong> — <code>host.docker.internal</code> may not be resolving on Linux. Add <code>extra_hosts: ["host.docker.internal:host-gateway"]</code> to the service in <code>docker-compose.yml</code>.</p>
<h2>Production Deployment Options</h2>
<p>The <code>docker compose up</code> approach works well for personal use and development. When you are ready to deploy to a server or the cloud, here are your main options.</p>
<h3>Docker Swarm</h3>
<p>Docker Swarm is the simplest step up from Compose. It lets you deploy across multiple machines with minimal changes to your existing Compose file:</p>
<pre><code class="language-bash">docker swarm init
docker stack deploy -c docker-compose.yml morning-brief
</code></pre>
<h3>Kubernetes</h3>
<p>For production at scale, Kubernetes gives you more control over scheduling, scaling, and fault tolerance. Use Kubernetes <strong>Jobs</strong> (not Deployments) for batch agents that run once and exit. Set resource requests and limits on each container so the cluster scheduler can allocate resources efficiently. Store API keys in <strong>Kubernetes Secrets</strong>, and use <strong>CronJobs</strong> for scheduled daily execution — they work like cron but are managed by the cluster.</p>
<h3>Cloud Platforms</h3>
<p>All major cloud providers offer managed container services that can run this pipeline:</p>
<p><strong>AWS</strong> — ECS Fargate with scheduled tasks for serverless execution, or EKS for managed Kubernetes.</p>
<p><strong>Azure</strong> — Azure Container Instances for simple runs, or AKS for managed Kubernetes.</p>
<p><strong>GCP</strong> — Cloud Run Jobs for serverless batch processing, or GKE for managed Kubernetes.</p>
<h2>Conclusion and Next Steps</h2>
<p>In this handbook, you built a multi-agent AI system from scratch. You created four specialized Python agents, containerized each one with Docker, orchestrated them with Docker Compose, and added secrets handling, structured logging, retry logic, and graceful fallbacks.</p>
<p>The core patterns you learned — separation of concerns, containerized agents, shared-volume communication, and defensive coding against external APIs — apply far beyond this specific use case. Any time you need a reliable, modular, and reproducible AI workflow, these patterns are a solid foundation.</p>
<p>Here are some directions to explore next:</p>
<p><strong>Agent collaboration frameworks</strong> — Tools like CrewAI and LangGraph let you build agents that delegate tasks to each other, negotiate priorities, and collaborate in more sophisticated ways.</p>
<p><strong>Local and fine-tuned models</strong> — Experiment with Ollama or vLLM to run models locally. Fine-tune a small model specifically for summarization to get better results at lower cost.</p>
<p><strong>Event-driven architectures</strong> — Replace the shared volume with Redis or RabbitMQ so agents react to events in real time rather than running on a schedule.</p>
<p><strong>Feedback loops</strong> — Add an agent that evaluates the quality of the daily digest and adjusts the Summarizer's prompts over time. This is how production agent systems learn and improve.</p>


                        </section>
                        
                            <div class="sidebar">
                                
                                    
                                    <script>var localizedAdText = "ADVERTISEMENT";</script>
                                
                            </div>
                        
                    </div>
                    <hr>
                    
                        <div class="post-full-author-header" data-test-label="author-header-with-bio">
                            
                                
    
    
    

    <section class="author-card" data-test-label="author-card">
        
            
    <img srcset="https://cdn.hashnode.com/res/hashnode/image/upload/v1748785611098/171b728f-5b91-434d-8f3a-1e991f0a507f.jpeg?w=500&h=500&fit=crop&crop=entropy&auto=compress,format&format=webp 60w" sizes="60px" src="https://cdn.hashnode.com/res/hashnode/image/upload/v1748785611098/171b728f-5b91-434d-8f3a-1e991f0a507f.jpeg?w=500&h=500&fit=crop&crop=entropy&auto=compress,format&format=webp" class="author-profile-image" alt="Balajee Asish Brahmandam" width="768" height="1024" onerror="this.style.display='none'" loading="lazy" data-test-label="profile-image">
  
        

        <section class="author-card-content ">
            <span class="author-card-name">
                <a href="/news/author/Balajeeasish/" data-test-label="profile-link">
                    
                        Balajee Asish Brahmandam
                    
                </a>
            </span>
            
                
                    <p data-test-label="default-bio">
                        Read <a href="/news/author/Balajeeasish/">more posts</a>.
                    </p>
                
            
        </section>
    </section>

                            
                        </div>
                        <hr>
                    

                    
                    
                        
    


<p data-test-label="social-row-cta" class="social-row">
    If this article was helpful, <button id="tweet-btn" class="cta-button" data-test-label="tweet-button">share it</button>.
</p>


    
    <script>document.addEventListener("DOMContentLoaded",()=>{const t=document.getElementById("tweet-btn"),e=window.location,n="How%20to%20Build%20and%20Deploy%20a%20Multi-Agent%20AI%20System%20with%20Python%20and%20Docker".replace(/&#39;/g,"%27"),o="",i="",r=Boolean("");let a;if(r&&(o||i)){const t={originalPostAuthor:"",currentPostAuthor:"Balajee Asish Brahmandam"};a=encodeURIComponent(`Thank you ${o||t.originalPostAuthor} for writing this helpful article, and ${i||t.currentPostAuthor} for translating it.`)}else!r&&i&&(a=encodeURIComponent(`Thank you ${i} for writing this helpful article.`));const s=`window.open(\n    '${a?`https://x.com/intent/post?text=${a}%0A%0A${n}%0A%0A${e}`:`https://x.com/intent/post?text=${n}%0A%0A${e}`}',\n    'share-twitter',\n    'width=550, height=235'\n  ); return false;`;t.setAttribute("onclick",s)});</script>


                        

<div class="learn-cta-row" data-test-label="learn-cta-row">
    <p>
        Learn to code for free. freeCodeCamp's open source curriculum has helped more than 40,000 people get jobs as developers. <a href="https://www.freecodecamp.org/learn" class="cta-button" id="learn-to-code-cta" rel="noopener noreferrer" target="_blank">Get started</a>
    </p>
</div>

                    
                </section>
                
                    <div class="banner-ad-bottom">
                        
                            

<div class="ad-text" data-test-label="ad-text">ADVERTISEMENT</div>
<div style="display: block; height: auto" id="gam-ad-bottom">
</div>

                        
                    </div>
                
            </article>
        </div>
    </main>


            


<footer class="site-footer">
    <div class="footer-top">
        <div class="footer-desc-col">
            <p data-test-label="tax-exempt-status">freeCodeCamp is a donor-supported tax-exempt 501(c)(3) charity organization (United States Federal Tax Identification Number: 82-0779546)</p>
            <p data-test-label="mission-statement">Our mission: to help people learn to code for free. We accomplish this by creating thousands of videos, articles, and interactive coding lessons - all freely available to the public.</p>
            <p data-test-label="donation-initiatives">Donations to freeCodeCamp go toward our education initiatives, and help pay for servers, services, and staff.</p>
            <p class="footer-donation" data-test-label="donate-text">
                You can <a href="https://www.freecodecamp.org/donate/" class="inline" rel="noopener noreferrer" target="_blank">make a tax-deductible donation here</a>.
            </p>
        </div>
        <div class="trending-guides" data-test-label="trending-guides">
            <h2 id="trending-guides" class="col-header">Trending Books and Handbooks</h2>
            <ul class="trending-guides-articles" aria-labelledby="trending-guides">
                <li>
                    <a href="https://www.freecodecamp.org/news/build-consume-and-document-a-rest-api/" rel="noopener noreferrer" target="_blank">REST APIs
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/how-to-write-clean-code/" rel="noopener noreferrer" target="_blank">Clean Code
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-typescript-with-react-handbook/" rel="noopener noreferrer" target="_blank">TypeScript
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-javascript-for-beginners/" rel="noopener noreferrer" target="_blank">JavaScript
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/how-to-build-an-ai-chatbot-with-redis-python-and-gpt/" rel="noopener noreferrer" target="_blank">AI Chatbots
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/command-line-for-beginners/" rel="noopener noreferrer" target="_blank">Command Line
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/building-consuming-and-documenting-a-graphql-api/" rel="noopener noreferrer" target="_blank">GraphQL APIs
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/complete-guide-to-css-transform-functions-and-properties/" rel="noopener noreferrer" target="_blank">CSS Transforms
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/how-to-build-scalable-access-control-for-your-web-app/" rel="noopener noreferrer" target="_blank">Access Control
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/rest-api-design-best-practices-build-a-rest-api/" rel="noopener noreferrer" target="_blank">REST API Design
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/the-php-handbook/" rel="noopener noreferrer" target="_blank">PHP
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/the-java-handbook/" rel="noopener noreferrer" target="_blank">Java
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-linux-for-beginners-book-basic-to-advanced/" rel="noopener noreferrer" target="_blank">Linux
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/react-for-beginners-handbook/" rel="noopener noreferrer" target="_blank">React
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-continuous-integration-delivery-and-deployment/" rel="noopener noreferrer" target="_blank">CI/CD
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/the-docker-handbook/" rel="noopener noreferrer" target="_blank">Docker
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-golang-handbook/" rel="noopener noreferrer" target="_blank">Golang
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/the-python-handbook/" rel="noopener noreferrer" target="_blank">Python
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/get-started-with-nodejs/" rel="noopener noreferrer" target="_blank">Node.js
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/build-crud-operations-with-dotnet-core-handbook/" rel="noopener noreferrer" target="_blank">Todo APIs
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/how-to-use-classes-in-javascript-handbook/" rel="noopener noreferrer" target="_blank">JavaScript Classes
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/front-end-javascript-development-react-angular-vue-compared/" rel="noopener noreferrer" target="_blank">Front-End Libraries
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/the-express-handbook/" rel="noopener noreferrer" target="_blank">Express and Node.js
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/python-code-examples-sample-script-coding-tutorial-for-beginners/" rel="noopener noreferrer" target="_blank">Python Code Examples
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/clustering-in-python-a-machine-learning-handbook/" rel="noopener noreferrer" target="_blank">Clustering in Python
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/an-introduction-to-software-architecture-patterns/" rel="noopener noreferrer" target="_blank">Software Architecture
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/what-is-programming-tutorial-for-beginners/" rel="noopener noreferrer" target="_blank">Programming Fundamentals
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-to-code-book/" rel="noopener noreferrer" target="_blank">Coding Career Preparation
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/become-a-full-stack-developer-and-get-a-job/" rel="noopener noreferrer" target="_blank">Full-Stack Developer Guide
                    </a>
                </li>
                <li>
                    <a href="https://www.freecodecamp.org/news/learn-python-for-javascript-developers-handbook/" rel="noopener noreferrer" target="_blank">Python for JavaScript Devs
                    </a>
                </li>
            </ul>
            <div class="spacer" style="padding: 15px 0;"></div>
            <div>
                <h2 id="mobile-app" class="col-header">
                    Mobile App
                </h2>
                <div class="min-h-[1px] px-[15px] md:w-2/3 md:ml-[16.6%]">
                    <ul aria-labelledby="mobile-app" class="mobile-app-container">
                        <li>
                            <a href="https://apps.apple.com/us/app/freecodecamp/id6446908151?itsct=apps_box_link&itscg=30200" rel="noopener noreferrer" target="_blank">
                                <img src="https://cdn.freecodecamp.org/platform/universal/apple-store-badge.svg" lang="en" alt="Download on the App Store">
                            </a>
                        </li>
                        <li>
                            <a href="https://play.google.com/store/apps/details?id=org.freecodecamp" rel="noopener noreferrer" target="_blank">
                                <img src="https://cdn.freecodecamp.org/platform/universal/google-play-badge.svg" lang="en" alt="Get it on Google Play">
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <div class="footer-bottom">
        <h2 class="col-header" data-test-label="our-nonprofit">Our Charity</h2>
        <div class="our-nonprofit">

            <a href="https://hashnode.com/" rel="noopener noreferrer" target="_blank" data-test-label="powered-by">
                Publication powered by Hashnode
            </a>
            <a href="https://www.freecodecamp.org/news/about/" rel="noopener noreferrer" target="_blank" data-test-label="about">
                About
            </a>
            <a href="https://www.linkedin.com/school/free-code-camp/people/" rel="noopener noreferrer" target="_blank" data-test-label="alumni">
                Alumni Network
            </a>
            <a href="https://github.com/freeCodeCamp/" rel="noopener noreferrer" target="_blank" data-test-label="open-source">
                Open Source
            </a>
            <a href="https://www.freecodecamp.org/news/shop/" rel="noopener noreferrer" target="_blank" data-test-label="shop">
                Shop
            </a>
            <a href="https://www.freecodecamp.org/news/support/" rel="noopener noreferrer" target="_blank" data-test-label="support">
                Support
            </a>
            <a href="https://www.freecodecamp.org/news/sponsors/" rel="noopener noreferrer" target="_blank" data-test-label="sponsors">
                Sponsors
            </a>
            <a href="https://www.freecodecamp.org/news/academic-honesty-policy/" rel="noopener noreferrer" target="_blank" data-test-label="honesty">
                Academic Honesty
            </a>
            <a href="https://www.freecodecamp.org/news/code-of-conduct/" rel="noopener noreferrer" target="_blank" data-test-label="coc">
                Code of Conduct
            </a>
            <a href="https://www.freecodecamp.org/news/privacy-policy/" rel="noopener noreferrer" target="_blank" data-test-label="privacy">
                Privacy Policy
            </a>
            <a href="https://www.freecodecamp.org/news/terms-of-service/" rel="noopener noreferrer" target="_blank" data-test-label="tos">
                Terms of Service
            </a>
            <a href="https://www.freecodecamp.org/news/copyright-policy/" rel="noopener noreferrer" target="_blank" data-test-label="copyright">
                Copyright Policy
            </a>
        </div>
    </div>
</footer>

        </div>

        
        
        

        
        
    <script defer src="https://static.cloudflareinsights.com/beacon.min.js/v8c78df7c7c0f484497ecbca7046644da1771523124516" integrity="sha512-8DS7rgIrAmghBFwoOTujcf6D9rXvH8xm8JQ1Ja01h9QX8EzXldiszufYa4IFfKdLUKTTrnSFXLDkUEOTrZQ8Qg==" data-cf-beacon='{"version":"2024.11.0","token":"bdb993c6dde44e178aabd9555e75e4f4","server_timing":{"name":{"cfCacheStatus":true,"cfEdge":true,"cfExtPri":true,"cfL4":true,"cfOrigin":true,"cfSpeedBrain":true},"location_startswith":null}}' crossorigin="anonymous"></script>
</body>
</html>
