<!-- 
   GitHub Analyzer Bot
   A Telegram bot that analyzes GitHub profiles for authenticity, activity, AI/crypto usage, etc.
-->

<h1 align="center">🚀 GitHub Analyzer Bot</h1>

<p align="center">
  <img src="GitHub-Analyzer.png" alt="GitHub Analyzer Logo" width="150" style="border-radius:50%">
</p>

<p align="center">
  <strong>Analyze GitHub profiles directly from your Telegram chat!</strong><br/>
  <em>Assess authenticity, commit patterns, AI/Crypto usage, and more.</em>
</p>

<hr/>

<h2>✨ Features</h2>

<ul>
  <li>🔍 Detects AI &amp; Crypto references in languages or dependencies</li>
  <li>📊 Scores repositories based on readme depth, commit frequency, PR/Issue activity, stars, forks, and recent commits</li>
  <li>💯 Generates an overall authenticity score <strong>(0–100)</strong> with a detailed breakdown</li>
  <li>📈 Displays an ASCII bar chart of the user's language usage</li>
  <li>🤖 Supports both <strong>private messages</strong> and <strong>group chat commands</strong> with <code>/analyze</code></li>
  <li>⚠️ Provides warnings for suspicious patterns or low activity</li>
  <li>👁️ Each time a profile is scanned, the bot keeps track of the number of scans.</li>

</ul>

<h2>🚀 Getting Started</h2>

<ol>
  <li><strong>Clone</strong> or <strong>Download</strong> this repository.</li>
  <li><strong>Install Dependencies</strong>:
    <pre><code>pip install -r requirements.txt
</code></pre>
  </li>
  <li>Create a <strong><em>.env</em></strong> file with your Telegram and GitHub tokens:
    <pre><code>TELEGRAM_BOT_TOKEN=123456:ABC-YourBotToken
GITHUB_TOKEN=ghp_YourGitHubPersonalAccessToken
</code></pre>
    <small>(The <em>GITHUB_TOKEN</em> is optional but helps avoid rate limits.)</small>
  </li>
  <li>Run the bot:
    <pre><code>python main.py
</code></pre>
    <small>You should see <em>"Bot is running... Press Ctrl+C to stop."</em></small>
  </li>
</ol>

<h2>🤖 Usage</h2>

<ul>
  <li><strong>Private Chat</strong>: Send a GitHub username or link (<code>https://github.com/username</code>). The bot replies with a score and detailed breakdown.</li>
  <li><strong>Group Chat</strong>:
    <ul>
      <li>Use <code>/analyze &lt;GitHub user or link&gt;</code>. For example:
        <pre><code>/analyze octocat
/analyze https://github.com/octocat
</code></pre>
      </li>
      <li>The bot will reply in the group with the authenticity score and analysis.</li>
    </ul>
  </li>
</ul>

<h2>📜 Commands</h2>

| Command                     | Description                                 |
|-----------------------------|---------------------------------------------|
| <code>/start</code>         | Initial greeting and overview               |
| <code>/help</code>          | How to use the bot, examples, etc.          |
| <code>/analyze &lt;...&gt;</code> | Analyzes the specified GitHub profile and returns a score |

<h2>📝 Logs</h2>
<p>
  The bot logs important actions and errors to STDOUT, which can be viewed in your hosting platform's logs dashboard.
</p>

<h2>💡 Contributing</h2>
<p>
  Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.
</p>

<h2>⚖️ License</h2>
<p>
  This project is open-sourced under the <strong>MIT License</strong> – see the <em>LICENSE</em> file for details.
</p>

<hr/>

<p align="center">
  <em>Crafted with love &amp; curiosity. Happy analyzing!</em> <br/>
  <strong>© 2025</strong>
</p>
