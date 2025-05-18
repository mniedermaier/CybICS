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
    <div class="hero-buttons">
        <a href="{{ '/docs' | relative_url }}" class="primary-button">
            <i class="fas fa-book-open"></i> Get Started
        </a>
        <a href="https://github.com/mniedermaier/CybICS" class="secondary-button">
            <i class="fab fa-github"></i> View on GitHub
        </a>
    </div>
</div>

<section class="features-grid">
    <div class="feature-card">
        <h3><i class="fas fa-microscope"></i> Research Platform</h3>
        <p>Advanced simulation capabilities for industrial processes and cybersecurity research in a controlled environment.</p>
    </div>
    <div class="feature-card">
        <h3><i class="fas fa-shield-halved"></i> Security Training</h3>
        <p>Hands-on cybersecurity training platform for professionals to learn and practice in a safe environment.</p>
    </div>
    <div class="feature-card">
        <h3><i class="fas fa-puzzle-piece"></i> Integration</h3>
        <p>Seamless integration between physical and virtual components for realistic ICS scenarios.</p>
    </div>
    <div class="feature-card">
        <h3><i class="fas fa-network-wired"></i> Virtual Environment</h3>
        <p>Complete virtual environment setup with Docker containers for easy deployment and scaling.</p>
    </div>
</section>

<section class="why-section">
    <h2><i class="fas fa-star"></i> Why CybICS?</h2>
    <div class="why-grid">
        <div class="why-item">
            <h3><i class="fas fa-gift"></i> Free Forever</h3>
            <p>CybICS is and will always be free to use, modify, and distribute under an open-source license.</p>
        </div>
        <div class="why-item">
            <h3><i class="fas fa-code"></i> Open Source</h3>
            <p>Full transparency with open-source code. Contribute, customize, and improve the platform for everyone.</p>
        </div>
        <div class="why-item">
            <h3><i class="fas fa-bullseye"></i> Purpose-Built</h3>
            <p>Specifically designed for industrial control system security research and training.</p>
        </div>
        <div class="why-item">
            <h3><i class="fas fa-arrows-rotate"></i> Flexible</h3>
            <p>Adaptable to various scenarios and use cases, from education to professional training.</p>
        </div>
    </div>
</section>

<section class="get-started">
    <h2><i class="fas fa-rocket"></i> Getting Started</h2>
    <div class="steps-container">
        <div class="step">
            <h3><i class="fas fa-code-branch"></i> 1. Clone Repository</h3>
            <p>Get started by cloning our GitHub repository to your local machine.</p>
            <div class="code-block">
                <code>git clone https://github.com/mniedermaier/CybICS.git --recursive</code>
                <button class="copy-button" onclick="copyCode(this)">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        </div>
        <div class="step">
            <h3><i class="fas fa-cogs"></i> 2. Setup Environment</h3>
            <p>Use our Docker-based setup for quick deployment.</p>
            <div class="code-block">
                <code>cd CybICS</code>
                <button class="copy-button" onclick="copyCode(this)">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
            <div class="code-block">
                <code>docker-compose up -d</code>
                <button class="copy-button" onclick="copyCode(this)">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        </div>
        <div class="step">
            <h3><i class="fas fa-graduation-cap"></i> 3. Start Learning</h3>
            <p>Follow our comprehensive documentation to begin your journey.</p>
            <a href="{{ '/docs' | relative_url }}" class="cta-button">
                <i class="fas fa-book"></i> View Documentation
            </a>
        </div>
    </div>
</section>

<section class="community">
    <h2><i class="fas fa-users"></i> Join Our Community</h2>
    <p>CybICS is more than just a platform - it's a community of cybersecurity enthusiasts, researchers, and professionals.</p>
    <div class="community-links">
        <a href="https://github.com/mniedermaier/CybICS" class="community-button">
            <i class="fab fa-github"></i> GitHub
        </a>
        <a href="{{ '/docs' | relative_url }}" class="community-button">
            <i class="fas fa-book"></i> Documentation
        </a>
        <a href="{{ '/about' | relative_url }}" class="community-button">
            <i class="fas fa-info-circle"></i> About Us
        </a>
    </div>
</section>

<script>
function copyCode(button) {
    const codeBlock = button.parentElement.querySelector('code');
    const textArea = document.createElement('textarea');
    textArea.value = codeBlock.textContent;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    // Show feedback
    const originalIcon = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check"></i>';
    button.classList.add('copied');
    
    setTimeout(() => {
        button.innerHTML = originalIcon;
        button.classList.remove('copied');
    }, 2000);
}
</script> 