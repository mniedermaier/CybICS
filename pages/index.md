---
layout: default
title: Home
---

<div class="hero">
  <h1 class="hero-title">Welcome to CybICS</h1>
  <p class="hero-subtitle">Cyber Infrastructure Control System</p>
  <div class="hero-buttons">
    <a href="/docs" class="neu-button">Get Started</a>
    <a href="/about" class="neu-button">Learn More</a>
  </div>
</div>

<div class="features">
  <div class="feature-card neu">
    <i class="fas fa-shield-alt feature-icon"></i>
    <h2>Secure Infrastructure</h2>
    <p>Advanced security features to protect your cyber infrastructure</p>
  </div>
  
  <div class="feature-card neu">
    <i class="fas fa-chart-line feature-icon"></i>
    <h2>Real-time Monitoring</h2>
    <p>Comprehensive monitoring and analytics for your systems</p>
  </div>
  
  <div class="feature-card neu">
    <i class="fas fa-cogs feature-icon"></i>
    <h2>Easy Integration</h2>
    <p>Seamless integration with existing infrastructure</p>
  </div>
</div>

<div class="cta-section">
  <div class="cta-content neu">
    <h2>Ready to Get Started?</h2>
    <p>Join the growing community of CybICS users</p>
    <a href="/docs" class="neu-button">View Documentation</a>
  </div>
</div>

<section id="aboutme" class="section">
  <div class="container">
    <h2 class="section-title">About CybICS</h2>
    <div class="row">
      <div class="col-md-8">
        <p class="section-text">
          CybICS is a comprehensive solution for managing and monitoring cyber infrastructure. 
          Built with security and efficiency in mind, it provides real-time monitoring, 
          advanced security features, and seamless integration capabilities.
        </p>
      </div>
    </div>
  </div>
</section>

<section id="skills" class="section">
  <div class="container">
    <h2 class="section-title">Key Features</h2>
    <div class="row">
      <div class="col-md-4">
        <div class="skill-item">
          <i class="fas fa-shield-alt"></i>
          <h3>Enhanced Security</h3>
          <p>Advanced security features to protect your infrastructure</p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="skill-item">
          <i class="fas fa-tachometer-alt"></i>
          <h3>Real-time Monitoring</h3>
          <p>Monitor your systems in real-time with detailed metrics</p>
        </div>
      </div>
      <div class="col-md-4">
        <div class="skill-item">
          <i class="fas fa-cogs"></i>
          <h3>Easy Integration</h3>
          <p>Seamlessly integrate with your existing infrastructure</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section id="projects" class="section">
  <div class="container">
    <h2 class="section-title">Getting Started</h2>
    <div class="row">
      <div class="col-md-4">
        <div class="project-item">
          <div class="project-title">
            <i class="fas fa-download"></i>
            <h3>Clone the Repository</h3>
          </div>
          <div class="project-content">
            <div class="code-block">
              <code>git clone --recursive https://github.com/yourusername/CybICS.git</code>
              <button class="copy-button" onclick="copyCode(this)">Copy</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="project-item">
          <div class="project-title">
            <i class="fas fa-cube"></i>
            <h3>Run with Docker</h3>
          </div>
          <div class="project-content">
            <div class="code-block">
              <code>docker-compose up -d</code>
              <button class="copy-button" onclick="copyCode(this)">Copy</button>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="project-item">
          <div class="project-title">
            <i class="fas fa-book"></i>
            <h3>Read the Docs</h3>
          </div>
          <div class="project-content">
            <p>Check out our comprehensive documentation to learn more.</p>
            <a href="/docs" class="btn btn-primary">View Documentation</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<section id="contact" class="section">
  <div class="container">
    <h2 class="section-title">Join Our Community</h2>
    <div class="row">
      <div class="col-md-6">
        <div class="contact-item">
          <i class="fab fa-github"></i>
          <h3>GitHub</h3>
          <p>Contribute to the project and track issues</p>
          <a href="https://github.com/yourusername/CybICS" class="btn btn-primary">View on GitHub</a>
        </div>
      </div>
      <div class="col-md-6">
        <div class="contact-item">
          <i class="fab fa-discord"></i>
          <h3>Discord</h3>
          <p>Join our community chat</p>
          <a href="https://discord.gg/yourdiscord" class="btn btn-primary">Join Discord</a>
        </div>
      </div>
    </div>
  </div>
</section>

<script>
function copyCode(button) {
  const codeBlock = button.previousElementSibling;
  const textArea = document.createElement('textarea');
  textArea.value = codeBlock.textContent;
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea);
  
  button.classList.add('copied');
  button.textContent = 'Copied!';
  setTimeout(() => {
    button.classList.remove('copied');
    button.textContent = 'Copy';
  }, 2000);
}
</script> 