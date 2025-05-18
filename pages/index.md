---
layout: default
title: Home
---

<div class="hero-section">
    <div class="logo-container">
        <img src="{{ '/assets/images/CybICS_logo.png' | relative_url }}" alt="CybICS Logo" class="main-logo">
    </div>
    <h1 class="hero-title">Welcome to CybICS</h1>
    <p class="hero-subtitle">A Free and Open-Source Cyber-Physical Industrial Control System Platform</p>
</div>

<section class="features-grid">
    <div class="feature-card">
        <i class="feature-icon">🔬</i>
        <h3>Research Platform</h3>
        <p>Advanced simulation capabilities for industrial processes and cybersecurity research in a controlled environment.</p>
    </div>
    <div class="feature-card">
        <i class="feature-icon">🛡️</i>
        <h3>Security Training</h3>
        <p>Hands-on cybersecurity training platform for professionals to learn and practice in a safe environment.</p>
    </div>
    <div class="feature-card">
        <i class="feature-icon">🔄</i>
        <h3>Integration</h3>
        <p>Seamless integration between physical and virtual components for realistic ICS scenarios.</p>
    </div>
    <div class="feature-card">
        <i class="feature-icon">🌐</i>
        <h3>Virtual Environment</h3>
        <p>Complete virtual environment setup with Docker containers for easy deployment and scaling.</p>
    </div>
</section>

<section class="why-section">
    <h2>Why CybICS?</h2>
    <div class="why-grid">
        <div class="why-item">
            <h3>🆓 Free Forever</h3>
            <p>CybICS is and will always be free to use, modify, and distribute under an open-source license.</p>
        </div>
        <div class="why-item">
            <h3>🔓 Open Source</h3>
            <p>Full transparency with open-source code. Contribute, customize, and improve the platform for everyone.</p>
        </div>
        <div class="why-item">
            <h3>🎯 Purpose-Built</h3>
            <p>Specifically designed for industrial control system security research and training.</p>
        </div>
        <div class="why-item">
            <h3>🔄 Flexible</h3>
            <p>Adaptable to various scenarios and use cases, from education to professional training.</p>
        </div>
    </div>
</section>

<section class="get-started">
    <h2>Getting Started</h2>
    <div class="steps-container">
        <div class="step">
            <span class="step-number">1</span>
            <h3>Clone Repository</h3>
            <p>Get started by cloning our GitHub repository to your local machine.</p>
            <pre><code>git clone https://github.com/your-username/CybICS.git</code></pre>
        </div>
        <div class="step">
            <span class="step-number">2</span>
            <h3>Setup Environment</h3>
            <p>Use our Docker-based setup for quick deployment.</p>
            <pre><code>cd CybICS
docker-compose up -d</code></pre>
        </div>
        <div class="step">
            <span class="step-number">3</span>
            <h3>Start Learning</h3>
            <p>Follow our comprehensive documentation to begin your journey.</p>
            <a href="{{ '/docs' | relative_url }}" class="cta-button">View Documentation</a>
        </div>
    </div>
</section>

<section class="community">
    <h2>Join Our Community</h2>
    <p>CybICS is more than just a platform - it's a community of cybersecurity enthusiasts, researchers, and professionals.</p>
    <div class="community-links">
        <a href="https://github.com/your-username/CybICS" class="community-button">
            <span>GitHub</span>
        </a>
        <a href="{{ '/docs' | relative_url }}" class="community-button">
            <span>Documentation</span>
        </a>
        <a href="{{ '/about' | relative_url }}" class="community-button">
            <span>About Us</span>
        </a>
    </div>
</section> 