#!/usr/bin/env node
/**
 * Test script for Email MCP Server
 */

import { spawn } from 'child_process';
import { createInterface } from 'readline';

const server = spawn('node', ['email_mcp_server.js'], {
    cwd: process.cwd(),
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env }
});

const rl = createInterface({
    input: server.stdout,
    crlfDelay: Infinity
});

let messageId = 1;
let results = [];

function sendRequest(method, params = {}) {
    return new Promise((resolve, reject) => {
        const request = {
            jsonrpc: '2.0',
            id: messageId++,
            method,
            params
        };

        const timeout = setTimeout(() => {
            reject(new Error('Request timeout'));
        }, 10000);

        const onResponse = (line) => {
            try {
                const response = JSON.parse(line);
                if (response.id === request.id) {
                    clearTimeout(timeout);
                    server.stdout.removeListener('data', onData);
                    resolve(response);
                }
            } catch (e) {
                // Not JSON, skip
            }
        };

        const onData = (data) => {
            const lines = data.toString().split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    onResponse(line);
                }
            }
        };

        server.stdout.on('data', onData);
        server.stdin.write(JSON.stringify(request) + '\n');
    });
}

async function runTests() {
    console.log('=== Email MCP Server Tests ===\n');

    try {
        // Initialize connection
        console.log('Step 1: Initializing MCP connection...');
        const initResult = await sendRequest('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: {},
            clientInfo: { name: 'test-client', version: '1.0.0' }
        });
        console.log('Init response:', initResult.result ? 'OK' : 'FAIL');
        results.push({ step: 'Initialize', status: initResult.result ? 'PASS' : 'FAIL' });

        // List tools
        console.log('\nStep 2: Listing available tools...');
        const toolsResult = await sendRequest('tools/list', {});
        if (toolsResult.result && toolsResult.result.tools) {
            const toolNames = toolsResult.result.tools.map(t => t.name);
            console.log('Available tools:', toolNames.join(', '));
            results.push({ step: 'List tools', status: 'PASS' });
        } else {
            console.log('No tools found');
            results.push({ step: 'List tools', status: 'FAIL' });
        }

        // Test list_drafts
        console.log('\nStep 3: Testing list_drafts tool...');
        const listResult = await sendRequest('tools/call', {
            name: 'list_drafts',
            arguments: {}
        });
        if (listResult.result && listResult.result.content) {
            console.log('list_drafts response:', listResult.result.content[0].text);
            results.push({ step: 'list_drafts', status: 'PASS' });
        } else {
            console.log('list_drafts error:', listResult.error || 'Unknown error');
            results.push({ step: 'list_drafts', status: 'FAIL' });
        }

        // Test draft_email
        console.log('\nStep 4: Testing draft_email tool...');
        const draftResult = await sendRequest('tools/call', {
            name: 'draft_email',
            arguments: {
                to: 'test@example.com',
                subject: 'MCP Server Test',
                body: 'This is a test draft from AI Employee MCP server'
            }
        });
        if (draftResult.result && draftResult.result.content) {
            console.log('draft_email response:', draftResult.result.content[0].text);
            results.push({ step: 'draft_email', status: 'PASS' });
        } else {
            console.log('draft_email error:', draftResult.error || 'Unknown error');
            results.push({ step: 'draft_email', status: 'FAIL' });
        }

    } catch (error) {
        console.error('Test error:', error.message);
        results.push({ step: 'General', status: 'FAIL', error: error.message });
    }

    // Cleanup
    server.kill();

    // Print summary
    console.log('\n=== Test Summary ===');
    results.forEach(r => {
        console.log(`${r.step}: ${r.status}${r.error ? ' - ' + r.error : ''}`);
    });

    const allPassed = results.every(r => r.status === 'PASS');
    console.log('\nOverall:', allPassed ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED');
}

runTests().catch(console.error);
