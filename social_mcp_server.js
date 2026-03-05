#!/usr/bin/env node
/**
 * Social Media MCP Server
 * Connects Claude to Facebook, Instagram, and Twitter via watcher scripts
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const execAsync = promisify(exec);

// Base directories
const BASE_DIR = __dirname;
const APPROVED_DIR = path.join(BASE_DIR, 'Approved');
const BRIEFINGS_DIR = path.join(BASE_DIR, 'Briefings');
const LOGS_DIR = path.join(BASE_DIR, 'Logs');

// Ensure directories exist
if (!fs.existsSync(APPROVED_DIR)) {
  fs.mkdirSync(APPROVED_DIR, { recursive: true });
}
if (!fs.existsSync(BRIEFINGS_DIR)) {
  fs.mkdirSync(BRIEFINGS_DIR, { recursive: true });
}
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Logging utility
function logAction(action, details, result = null) {
  const logFile = path.join(LOGS_DIR, 'social_mcp_log.json');
  let logs = [];
  
  if (fs.existsSync(logFile)) {
    try {
      logs = JSON.parse(fs.readFileSync(logFile, 'utf-8'));
    } catch (e) {
      logs = [];
    }
  }
  
  logs.push({
    timestamp: new Date().toISOString(),
    action,
    details,
    result: result ? 'success' : 'error'
  });
  
  fs.writeFileSync(logFile, JSON.stringify(logs, null, 2));
}

// Tool definitions
const tools = [
  {
    name: 'post_facebook',
    description: 'Posts approved content from Approved/ folder to Facebook. Reads .md files and executes posts via social_media_watcher.py.',
    inputSchema: zodToJsonSchema(z.object({
      filename: z.string().optional().describe('Specific pending file to process (optional)')
    }))
  },
  {
    name: 'post_instagram',
    description: 'Posts approved content from Approved/ folder to Instagram. Reads .md files and executes posts via social_media_watcher.py.',
    inputSchema: zodToJsonSchema(z.object({
      filename: z.string().optional().describe('Specific pending file to process (optional)')
    }))
  },
  {
    name: 'post_tweet',
    description: 'Posts approved content from Approved/ folder to Twitter. Reads .md files and executes tweets via twitter_watcher.py.',
    inputSchema: zodToJsonSchema(z.object({
      filename: z.string().optional().describe('Specific pending file to process (optional)')
    }))
  },
  {
    name: 'get_social_summary',
    description: 'Reads all 3 summary files from Briefings/ (facebook_summary.md, instagram_summary.md, twitter_summary.md) and returns a combined social media report.',
    inputSchema: zodToJsonSchema(z.object({}))
  }
];

// Execute Python script helper
async function runPythonScript(script, args = []) {
  return new Promise((resolve, reject) => {
    const command = `python "${path.join(BASE_DIR, script)}" ${args.map(a => `"${a}"`).join(' ')}`;
    exec(command, { cwd: BASE_DIR }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(stderr || error.message));
      } else {
        try {
          resolve(JSON.parse(stdout));
        } catch (e) {
          resolve({ output: stdout, error: stderr });
        }
      }
    });
  });
}

// Read approved file content
function readApprovedFile(filename) {
  const filepath = path.join(APPROVED_DIR, filename);
  if (!fs.existsSync(filepath)) {
    throw new Error(`File not found: ${filename}`);
  }
  return fs.readFileSync(filepath, 'utf-8');
}

// Parse approved file to extract content
function parseApprovedFile(content) {
  const result = {
    platform: null,
    text: null,
    image: null
  };
  
  const lines = content.split('\n');
  let currentSection = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (line === '## Platform' || line.toLowerCase() === 'facebook' || line.toLowerCase() === 'instagram') {
      if (line.startsWith('##')) {
        currentSection = 'platform';
      } else {
        result.platform = line.toLowerCase();
      }
    } else if (line === '## Content') {
      currentSection = 'content';
    } else if (line === '## Image') {
      currentSection = 'image';
    } else if (line.startsWith('## ')) {
      currentSection = null;
    } else if (line && currentSection === 'content' && !result.text) {
      result.text = line;
    } else if (line && currentSection === 'image' && line.toLowerCase() !== 'none') {
      result.image = line;
    }
  }
  
  return result;
}

// Tool handlers
async function handlePostFacebook(args) {
  try {
    // Process pending tweets via social_media_watcher.py
    const result = await runPythonScript('social_media_watcher.py', ['process']);
    
    // Read all approved files and identify Facebook posts
    const files = fs.readdirSync(APPROVED_DIR);
    let processedCount = 0;
    let facebookPosts = [];
    
    for (const file of files) {
      if (file.endsWith('.md') && !file.endsWith('.processed')) {
        const content = readApprovedFile(file);
        const parsed = parseApprovedFile(content);
        
        if (parsed.platform === 'facebook') {
          facebookPosts.push({ file, ...parsed });
        }
      }
    }
    
    logAction('post_facebook', { 
      files_found: facebookPosts.length,
      processed: result 
    }, true);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'processed',
          facebook_posts_found: facebookPosts.length,
          posts: facebookPosts.map(p => ({
            file: p.file,
            text_preview: p.text?.substring(0, 100) || 'N/A',
            has_image: !!p.image
          })),
          message: 'Run social_media_watcher.py process command. Check Logs/social_log.json for actual post results.',
          note: 'Facebook posts require META_ACCESS_TOKEN and META_PAGE_ID environment variables'
        }, null, 2)
      }]
    };
  } catch (error) {
    logAction('post_facebook', { error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error processing Facebook posts: ${error.message}` }],
      isError: true
    };
  }
}

async function handlePostInstagram(args) {
  try {
    // Process pending posts via social_media_watcher.py
    const result = await runPythonScript('social_media_watcher.py', ['process']);
    
    // Read all approved files and identify Instagram posts
    const files = fs.readdirSync(APPROVED_DIR);
    let instagramPosts = [];
    
    for (const file of files) {
      if (file.endsWith('.md') && !file.endsWith('.processed')) {
        const content = readApprovedFile(file);
        const parsed = parseApprovedFile(content);
        
        if (parsed.platform === 'instagram') {
          instagramPosts.push({ file, ...parsed });
        }
      }
    }
    
    logAction('post_instagram', { 
      files_found: instagramPosts.length,
      processed: result 
    }, true);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'processed',
          instagram_posts_found: instagramPosts.length,
          posts: instagramPosts.map(p => ({
            file: p.file,
            text_preview: p.text?.substring(0, 100) || 'N/A',
            image: p.image || 'N/A'
          })),
          message: 'Run social_media_watcher.py process command. Check Logs/social_log.json for actual post results.',
          note: 'Instagram posts require META_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID environment variables'
        }, null, 2)
      }]
    };
  } catch (error) {
    logAction('post_instagram', { error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error processing Instagram posts: ${error.message}` }],
      isError: true
    };
  }
}

async function handlePostTweet(args) {
  try {
    // Process pending tweets via twitter_watcher.py
    const result = await runPythonScript('twitter_watcher.py', ['process']);
    
    // Read all approved tweet files
    const files = fs.readdirSync(APPROVED_DIR);
    let tweetFiles = [];
    
    for (const file of files) {
      if (file.startsWith('tweet_') && file.endsWith('.md') && !file.endsWith('.processed')) {
        const content = readApprovedFile(file);
        const parsed = parseApprovedFile(content);
        tweetFiles.push({ file, ...parsed });
      }
    }
    
    logAction('post_tweet', { 
      files_found: tweetFiles.length,
      processed: result 
    }, true);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'processed',
          tweets_found: tweetFiles.length,
          tweets: tweetFiles.map(t => ({
            file: t.file,
            text_preview: t.text?.substring(0, 100) || 'N/A'
          })),
          message: 'Run twitter_watcher.py process command. Check Logs/twitter_log.json for actual tweet results.',
          note: 'Tweets require TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET, and TWITTER_BEARER_TOKEN environment variables'
        }, null, 2)
      }]
    };
  } catch (error) {
    logAction('post_tweet', { error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error processing tweets: ${error.message}` }],
      isError: true
    };
  }
}

async function handleGetSocialSummary(args) {
  try {
    const summaries = {
      facebook: null,
      instagram: null,
      twitter: null,
      errors: []
    };
    
    // Read Facebook summary
    const fbPath = path.join(BRIEFINGS_DIR, 'facebook_summary.md');
    if (fs.existsSync(fbPath)) {
      summaries.facebook = fs.readFileSync(fbPath, 'utf-8');
    } else {
      summaries.errors.push('Facebook summary not found. Run: python social_media_watcher.py facebook-summary');
    }
    
    // Read Instagram summary
    const igPath = path.join(BRIEFINGS_DIR, 'instagram_summary.md');
    if (fs.existsSync(igPath)) {
      summaries.instagram = fs.readFileSync(igPath, 'utf-8');
    } else {
      summaries.errors.push('Instagram summary not found. Run: python social_media_watcher.py instagram-summary');
    }
    
    // Read Twitter summary
    const twPath = path.join(BRIEFINGS_DIR, 'twitter_summary.md');
    if (fs.existsSync(twPath)) {
      summaries.twitter = fs.readFileSync(twPath, 'utf-8');
    } else {
      summaries.errors.push('Twitter summary not found. Run: python twitter_watcher.py summary');
    }
    
    // Create combined report
    const combinedReport = `# Combined Social Media Summary

**Generated:** ${new Date().toISOString()}

---

${summaries.facebook ? '## Facebook\n\n' + summaries.facebook : '## Facebook\n\n*No summary available*\n'}

---

${summaries.instagram ? '## Instagram\n\n' + summaries.instagram : '## Instagram\n\n*No summary available*\n'}

---

${summaries.twitter ? '## Twitter\n\n' + summaries.twitter : '## Twitter\n\n*No summary available*\n'}

---

## Notes
${summaries.errors.length > 0 ? summaries.errors.map(e => `- ${e}`).join('\n') : 'All summaries available'}
`;
    
    logAction('get_social_summary', {
      facebook: !!summaries.facebook,
      instagram: !!summaries.instagram,
      twitter: !!summaries.twitter,
      errors: summaries.errors.length
    }, true);
    
    return {
      content: [{
        type: 'text',
        text: combinedReport
      }]
    };
  } catch (error) {
    logAction('get_social_summary', { error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error getting social summary: ${error.message}` }],
      isError: true
    };
  }
}

// Main server setup
async function main() {
  const server = new Server(
    {
      name: 'social-mcp-server',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // List tools handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
  });

  // Call tool handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;

    switch (name) {
      case 'post_facebook':
        return handlePostFacebook(args);
      case 'post_instagram':
        return handlePostInstagram(args);
      case 'post_tweet':
        return handlePostTweet(args);
      case 'get_social_summary':
        return handleGetSocialSummary(args);
      default:
        return {
          content: [{ type: 'text', text: `Unknown tool: ${name}` }],
          isError: true
        };
    }
  });

  // Start server
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Social Media MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
