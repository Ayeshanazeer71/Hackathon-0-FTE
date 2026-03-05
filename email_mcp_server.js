#!/usr/bin/env node
/**
 * Email MCP Server for Personal AI Employee System
 * 
 * Provides email sending and draft management capabilities via Gmail.
 * 
 * GMAIL SETUP INSTRUCTIONS:
 * 1. Go to https://myaccount.google.com/apppasswords
 * 2. Select "Mail" and your device
 * 3. Generate an app password (16 characters)
 * 4. Set environment variables:
 *    - GMAIL_USER=your.email@gmail.com
 *    - GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx (the 16-char password)
 * 
 * SECURITY NOTES:
 * - Never share your app password
 * - Only approved contacts can receive emails (see approved_contacts.txt)
 * - All send attempts are logged to Logs/email_log.json
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import nodemailer from 'nodemailer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { config } from 'dotenv';

// Load .env file
config();

// Get directory name (ESM equivalent of __dirname)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const DRAFTS_DIR = path.join(__dirname, 'Drafts');
const LOGS_DIR = path.join(__dirname, 'Logs');
const APPROVED_CONTACTS_FILE = path.join(__dirname, 'approved_contacts.txt');
const EMAIL_LOG_FILE = path.join(LOGS_DIR, 'email_log.json');

// Ensure directories exist
function ensureDirectories() {
    if (!fs.existsSync(DRAFTS_DIR)) {
        fs.mkdirSync(DRAFTS_DIR, { recursive: true });
        console.error(`Created Drafts directory: ${DRAFTS_DIR}`);
    }
    if (!fs.existsSync(LOGS_DIR)) {
        fs.mkdirSync(LOGS_DIR, { recursive: true });
        console.error(`Created Logs directory: ${LOGS_DIR}`);
    }
}

// Load approved contacts
function loadApprovedContacts() {
    if (!fs.existsSync(APPROVED_CONTACTS_FILE)) {
        // Create empty approved contacts file with instructions
        const instructions = `# Approved Email Contacts
# Add one email address per line
# Example:
# john.doe@example.com
# jane.smith@company.com

`;
        fs.writeFileSync(APPROVED_CONTACTS_FILE, instructions, 'utf-8');
        console.error(`Created approved_contacts.txt with instructions`);
        return new Set();
    }

    const content = fs.readFileSync(APPROVED_CONTACTS_FILE, 'utf-8');
    const contacts = new Set();
    
    content.split('\n').forEach(line => {
        const trimmed = line.trim();
        // Skip comments and empty lines
        if (trimmed && !trimmed.startsWith('#')) {
            contacts.add(trimmed.toLowerCase());
        }
    });

    return contacts;
}

// Log email send attempt
function logEmailAttempt(to, subject, status, error = null) {
    ensureDirectories();
    
    let logs = [];
    if (fs.existsSync(EMAIL_LOG_FILE)) {
        try {
            const content = fs.readFileSync(EMAIL_LOG_FILE, 'utf-8');
            logs = JSON.parse(content);
        } catch (e) {
            logs = [];
        }
    }

    logs.push({
        timestamp: new Date().toISOString(),
        to,
        subject,
        status,
        error: error ? String(error) : null
    });

    // Keep only last 1000 entries
    if (logs.length > 1000) {
        logs = logs.slice(-1000);
    }

    fs.writeFileSync(EMAIL_LOG_FILE, JSON.stringify(logs, null, 2), 'utf-8');
}

// Create Gmail transporter
function createTransporter() {
    const gmailUser = process.env.GMAIL_USER;
    const gmailPassword = process.env.GMAIL_APP_PASSWORD;

    if (!gmailUser || !gmailPassword) {
        throw new Error(
            'Gmail credentials not configured. Please set GMAIL_USER and GMAIL_APP_PASSWORD environment variables. ' +
            'See instructions at the top of email_mcp_server.js'
        );
    }

    return nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: gmailUser,
            pass: gmailPassword
        }
    });
}

// Check if recipient is approved
function isApprovedContact(email) {
    const approved = loadApprovedContacts();
    return approved.has(email.toLowerCase());
}

// Create draft file
function createDraftFile(to, subject, body) {
    ensureDirectories();
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const safeSubject = subject.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
    const filename = `draft_${safeSubject}_${timestamp}.md`;
    const filepath = path.join(DRAFTS_DIR, filename);

    const content = `---
type: email_draft
to: ${to}
subject: ${subject}
created: ${new Date().toISOString()}
status: draft
---

## Email Content

${body}

---
*Draft created by Email MCP Server*
`;

    fs.writeFileSync(filepath, content, 'utf-8');
    return filepath;
}

// MCP Server instance
const server = new Server(
    {
        name: 'email-mcp-server',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: 'send_email',
                description: 'Send an email via Gmail. Recipient must be in approved_contacts.txt or it will be saved as draft instead.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject line'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content'
                        }
                    },
                    required: ['to', 'subject', 'body']
                }
            },
            {
                name: 'draft_email',
                description: 'Save an email draft to the Drafts folder without sending.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject line'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content'
                        }
                    },
                    required: ['to', 'subject', 'body']
                }
            },
            {
                name: 'list_drafts',
                description: 'List all draft email files in the Drafts folder.',
                inputSchema: {
                    type: 'object',
                    properties: {}
                }
            }
        ]
    };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case 'send_email': {
                const { to, subject, body } = args;

                // Validate email format (basic check)
                if (!to || !to.includes('@')) {
                    logEmailAttempt(to, subject, 'failed', 'Invalid email address');
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `Error: Invalid email address "${to}"`
                            }
                        ],
                        isError: true
                    };
                }

                // Check if recipient is approved
                if (!isApprovedContact(to)) {
                    console.error(`WARNING: Recipient "${to}" not in approved_contacts.txt. Saving as draft instead.`);
                    
                    // Save as draft instead
                    const draftPath = createDraftFile(to, subject, body);
                    logEmailAttempt(to, subject, 'saved_as_draft', 'Recipient not approved');
                    
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `⚠️ Recipient "${to}" is not in approved_contacts.txt. Email saved as draft instead: ${draftPath}\n\nTo send emails to this recipient, add their address to approved_contacts.txt first.`
                            }
                        ]
                    };
                }

                // Send the email
                try {
                    const transporter = createTransporter();
                    
                    await transporter.sendMail({
                        from: process.env.GMAIL_USER,
                        to,
                        subject,
                        text: body,
                        html: body.replace(/\n/g, '<br>')
                    });

                    const timestamp = new Date().toISOString();
                    logEmailAttempt(to, subject, 'success');

                    return {
                        content: [
                            {
                                type: 'text',
                                text: `✅ Email sent successfully to ${to}\nSubject: ${subject}\nTimestamp: ${timestamp}`
                            }
                        ]
                    };

                } catch (sendError) {
                    logEmailAttempt(to, subject, 'failed', sendError.message);
                    throw sendError;
                }
            }

            case 'draft_email': {
                const { to, subject, body } = args;

                const draftPath = createDraftFile(to, subject, body);
                
                return {
                    content: [
                        {
                            type: 'text',
                            text: `📝 Draft saved successfully\nFile: ${draftPath}\nTo: ${to}\nSubject: ${subject}`
                        }
                    ]
                };
            }

            case 'list_drafts': {
                ensureDirectories();
                
                let files = [];
                try {
                    files = fs.readdirSync(DRAFTS_DIR)
                        .filter(f => f.endsWith('.md'))
                        .sort((a, b) => {
                            const statA = fs.statSync(path.join(DRAFTS_DIR, a));
                            const statB = fs.statSync(path.join(DRAFTS_DIR, b));
                            return statB.mtime - statA.mtime; // Newest first
                        });
                } catch (e) {
                    files = [];
                }

                if (files.length === 0) {
                    return {
                        content: [
                            {
                                type: 'text',
                                text: 'No drafts found in Drafts folder.'
                            }
                        ]
                    };
                }

                const fileList = files.map((f, i) => `${i + 1}. ${f}`).join('\n');
                return {
                    content: [
                        {
                            type: 'text',
                            text: `📋 Draft Files (${files.length} total):\n\n${fileList}`
                        }
                    ]
                };
            }

            default:
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Error: Unknown tool "${name}"`
                        }
                    ],
                    isError: true
                };
        }
    } catch (error) {
        console.error(`Error in tool ${name}:`, error);
        return {
            content: [
                {
                    type: 'text',
                    text: `Error: ${error.message}`
                }
            ],
            isError: true
        };
    }
});

// Start server
async function main() {
    console.error('Starting Email MCP Server...');
    console.error('Gmail User:', process.env.GMAIL_USER ? 'configured' : 'NOT CONFIGURED');
    
    ensureDirectories();
    loadApprovedContacts();

    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('Email MCP Server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
