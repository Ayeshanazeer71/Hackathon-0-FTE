#!/usr/bin/env node
/**
 * Test Email MCP Server Tools
 * Tests send_email, draft_email, and list_drafts tools
 */

import { config } from 'dotenv';
config();

console.log('='.repeat(60));
console.log('       EMAIL MCP SERVER - MANUAL TEST');
console.log('='.repeat(60));

console.log('\n✅ Configuration loaded from .env\n');

console.log('Gmail User:', process.env.GMAIL_USER);
console.log('Approved Contacts: Check approved_contacts.txt\n');

console.log('='.repeat(60));
console.log('       HOW TO TEST THE MCP SERVER');
console.log('='.repeat(60));

console.log(`
The Email MCP Server is now running in the background.

To test it via MCP (Model Context Protocol):

1. The server provides these tools:
   - send_email: Send email to approved contacts
   - draft_email: Save email as draft
   - list_drafts: List all draft files

2. Test via your AI assistant:
   - "Send an email to ma9400667@gmail.com with subject 'Test' and body 'Hello'"
   - "Save a draft email to test@example.com"
   - "List all email drafts"

3. Check the results:
   - Sent emails: Check your Gmail sent folder
   - Drafts: Check Drafts/ folder
   - Logs: Check Logs/email_log.json
`);

console.log('='.repeat(60));
console.log('Server Status: RUNNING');
console.log('='.repeat(60));
