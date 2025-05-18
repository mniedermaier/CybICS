---
layout: default
title: Documentation
subtitle: Learn how to use CybICS
---

<section id="documentation" class="section">
  <div class="container">
    <div class="row">
      <div class="col-md-8">
        <h2 class="section-title">Getting Started</h2>
        <div class="documentation-content">
          <h3>Installation</h3>
          <p>Follow these steps to get CybICS up and running:</p>
          
          <div class="code-block">
            <h4>1. Clone the Repository</h4>
            <code>git clone --recursive https://github.com/yourusername/CybICS.git</code>
            <button class="copy-button" onclick="copyCode(this)">Copy</button>
          </div>

          <div class="code-block">
            <h4>2. Navigate to Project Directory</h4>
            <code>cd CybICS</code>
            <button class="copy-button" onclick="copyCode(this)">Copy</button>
          </div>

          <div class="code-block">
            <h4>3. Start with Docker</h4>
            <code>docker-compose up -d</code>
            <button class="copy-button" onclick="copyCode(this)">Copy</button>
          </div>

          <h3>Configuration</h3>
          <p>Learn how to configure CybICS for your specific needs:</p>
          <ul>
            <li>System Requirements</li>
            <li>Network Setup</li>
            <li>Security Settings</li>
            <li>Custom Integrations</li>
          </ul>

          <h3>Usage</h3>
          <p>Explore the main features and capabilities:</p>
          <ul>
            <li>Dashboard Overview</li>
            <li>Monitoring Tools</li>
            <li>Security Features</li>
            <li>API Documentation</li>
          </ul>
        </div>
      </div>

      <div class="col-md-4">
        <div class="documentation-sidebar">
          <h3>Quick Links</h3>
          <ul>
            <li><a href="#installation">Installation</a></li>
            <li><a href="#configuration">Configuration</a></li>
            <li><a href="#usage">Usage</a></li>
            <li><a href="#troubleshooting">Troubleshooting</a></li>
          </ul>

          <h3>Resources</h3>
          <ul>
            <li><a href="https://github.com/yourusername/CybICS">GitHub Repository</a></li>
            <li><a href="https://github.com/yourusername/CybICS/issues">Issue Tracker</a></li>
            <li><a href="https://discord.gg/yourdiscord">Community Discord</a></li>
          </ul>
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