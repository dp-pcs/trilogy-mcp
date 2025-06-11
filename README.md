# Trilogy AI MCP Server

This repository provides a Model Context Protocol (MCP) server that exposes the Trilogy AI Center of Excellence Substack as tools and resources. The project can be run locally for experimentation or deployed to AWS Elastic Beanstalk.

## Features

* **Resources**
  * `trilogy://publications` – JSON list of all Trilogy AI Substack posts
  * `trilogy://stats` – Statistical overview of the publication history
* **Tools**
  * `list_trilogy_posts()` – list recent posts
  * `read_trilogy_article()` – fetch the full text of an article
  * `search_trilogy_articles()` – search posts by title or summary
  * `analyze_trilogy_content()` – basic word and sentence statistics
* **Prompts** – prebuilt prompts for content analysis and debugging

## Local Setup

1. Install Python 3.12+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server with the MCP Inspector:
   ```bash
   mcp dev substack_mcp.py
   ```
   The Inspector UI will open in your browser. Use it to call tools and prompts.

## Deployment to Elastic Beanstalk

1. Install the [AWS Elastic Beanstalk CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html) and configure your AWS credentials.
2. Initialize the EB project:
   ```bash
   eb init -p docker trilogy-mcp
   ```
   Choose a region and create a new application when prompted.
3. Create the environment and deploy:
   ```bash
   eb create trilogy-mcp-env
   eb deploy
   ```
   The Dockerfile in this repo runs the server using `mcp run substack_mcp.py:server --transport sse`.
4. After deployment completes, note the environment URL. You can use it with the Claude Desktop or ChatGPT MCP connectors.

## Debugging

Run the prompt `debug_trilogy_mcp_server()` in the inspector for a checklist of commands to try when troubleshooting the server.
