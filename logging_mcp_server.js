#!/usr/bin/env node
/**
 * Logging MCP Server
 * Centralized logging and audit trail for AI Employee system
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Base directories
const BASE_DIR = __dirname;
const LOGS_DIR = path.join(BASE_DIR, 'Logs');

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Get today's log file path
function getLogFilePath(date = new Date()) {
  const dateStr = date.toISOString().split('T')[0];
  return path.join(LOGS_DIR, `${dateStr}.json`);
}

// Parse date string (YYYY-MM-DD)
function parseDate(dateStr) {
  const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) {
    throw new Error(`Invalid date format: ${dateStr}. Use YYYY-MM-DD`);
  }
  return new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
}

// Read log file for a specific date
function readLogFile(date) {
  const logPath = getLogFilePath(date);
  if (!fs.existsSync(logPath)) {
    return [];
  }
  try {
    const content = fs.readFileSync(logPath, 'utf-8');
    return JSON.parse(content);
  } catch (e) {
    return [];
  }
}

// Write log file for a specific date
function writeLogFile(date, entries) {
  const logPath = getLogFilePath(date);
  fs.writeFileSync(logPath, JSON.stringify(entries, null, 2), 'utf-8');
}

// Append entry to log file
function appendLogEntry(entry) {
  const date = entry.timestamp ? new Date(entry.timestamp) : new Date();
  const entries = readLogFile(date);
  entries.push(entry);
  writeLogFile(date, entries);
  return entry;
}

// Tool definitions
const tools = [
  {
    name: 'write_log',
    description: 'Appends a log entry to ./Logs/YYYY-MM-DD.json with timestamp, action, actor, and result fields.',
    inputSchema: zodToJsonSchema(z.object({
      action: z.string().describe('The action being logged'),
      actor: z.string().describe('Who or what performed the action'),
      result: z.enum(['success', 'error', 'warning', 'info']).describe('Result of the action'),
      details: z.object({}).optional().describe('Additional details about the action'),
      timestamp: z.string().optional().describe('ISO timestamp (defaults to now)')
    }))
  },
  {
    name: 'read_logs',
    description: 'Reads log entries for a given date range. Returns all entries between start_date and end_date.',
    inputSchema: zodToJsonSchema(z.object({
      start_date: z.string().describe('Start date in YYYY-MM-DD format'),
      end_date: z.string().optional().describe('End date in YYYY-MM-DD format (defaults to start_date)'),
      action_filter: z.string().optional().describe('Filter by action type (optional)'),
      actor_filter: z.string().optional().describe('Filter by actor (optional)'),
      result_filter: z.enum(['success', 'error', 'warning', 'info']).optional().describe('Filter by result (optional)')
    }))
  },
  {
    name: 'get_audit_summary',
    description: 'Counts actions by type for a given week. Returns summary statistics including total actions, actions by type, actors, and results.',
    inputSchema: zodToJsonSchema(z.object({
      week_start: z.string().describe('Start of week in YYYY-MM-DD format (Monday)'),
      include_details: z.boolean().optional().default(false).describe('Include detailed breakdown (optional)')
    }))
  }
];

// Tool handlers
async function handleWriteLog(args) {
  try {
    const { action, actor, result, details = {}, timestamp } = args;
    
    const entry = {
      timestamp: timestamp || new Date().toISOString(),
      action,
      actor,
      result,
      details
    };
    
    appendLogEntry(entry);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          message: 'Log entry written',
          entry: {
            timestamp: entry.timestamp,
            action: entry.action,
            actor: entry.actor,
            result: entry.result
          },
          log_file: getLogFilePath(new Date(entry.timestamp)).split(path.sep).pop()
        }, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error writing log: ${error.message}` }],
      isError: true
    };
  }
}

async function handleReadLogs(args) {
  try {
    const { start_date, end_date, action_filter, actor_filter, result_filter } = args;
    
    const start = parseDate(start_date);
    const end = end_date ? parseDate(end_date) : start;
    
    // Ensure end >= start
    if (end < start) {
      throw new Error('end_date must be >= start_date');
    }
    
    const allEntries = [];
    const currentDate = new Date(start);
    
    while (currentDate <= end) {
      const entries = readLogFile(currentDate);
      allEntries.push(...entries);
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Apply filters
    let filtered = allEntries;
    
    if (action_filter) {
      filtered = filtered.filter(e => e.action?.toLowerCase().includes(action_filter.toLowerCase()));
    }
    
    if (actor_filter) {
      filtered = filtered.filter(e => e.actor?.toLowerCase().includes(actor_filter.toLowerCase()));
    }
    
    if (result_filter) {
      filtered = filtered.filter(e => e.result === result_filter);
    }
    
    // Sort by timestamp
    filtered.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          success: true,
          query: {
            start_date,
            end_date: end_date || start_date,
            action_filter,
            actor_filter,
            result_filter
          },
          total_entries: filtered.length,
          entries: filtered
        }, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error reading logs: ${error.message}` }],
      isError: true
    };
  }
}

async function handleGetAuditSummary(args) {
  try {
    const { week_start, include_details = false } = args;
    
    const start = parseDate(week_start);
    const end = new Date(start);
    end.setDate(end.getDate() + 6); // 7 days total
    
    // Collect all entries for the week
    const allEntries = [];
    const currentDate = new Date(start);
    
    while (currentDate <= end) {
      const entries = readLogFile(currentDate);
      allEntries.push(...entries);
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    // Count by action type
    const actionsByType = {};
    const actionsByActor = {};
    const actionsByResult = {};
    const actionsByDate = {};
    
    for (const entry of allEntries) {
      // By action type
      const action = entry.action || 'unknown';
      actionsByType[action] = (actionsByType[action] || 0) + 1;
      
      // By actor
      const actor = entry.actor || 'unknown';
      actionsByActor[actor] = (actionsByActor[actor] || 0) + 1;
      
      // By result
      const result = entry.result || 'unknown';
      actionsByResult[result] = (actionsByResult[result] || 0) + 1;
      
      // By date
      const date = entry.timestamp?.split('T')[0] || 'unknown';
      actionsByDate[date] = (actionsByDate[date] || 0) + 1;
    }
    
    // Sort actions by count
    const sortedActions = Object.entries(actionsByType)
      .sort((a, b) => b[1] - a[1])
      .map(([action, count]) => ({ action, count }));
    
    const sortedActors = Object.entries(actionsByActor)
      .sort((a, b) => b[1] - a[1])
      .map(([actor, count]) => ({ actor, count }));
    
    const summary = {
      success: true,
      period: {
        start: week_start,
        end: end.toISOString().split('T')[0],
        days: 7
      },
      totals: {
        total_actions: allEntries.length,
        unique_actions: Object.keys(actionsByType).length,
        unique_actors: Object.keys(actionsByActor).length,
        avg_actions_per_day: (allEntries.length / 7).toFixed(1)
      },
      by_result: actionsByResult,
      top_actions: sortedActions.slice(0, 10),
      top_actors: sortedActors.slice(0, 10)
    };
    
    if (include_details) {
      summary.details = {
        all_actions: actionsByType,
        all_actors: actionsByActor,
        by_date: actionsByDate
      };
    }
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(summary, null, 2)
      }]
    };
  } catch (error) {
    return {
      content: [{ type: 'text', text: `Error getting audit summary: ${error.message}` }],
      isError: true
    };
  }
}

// Main server setup
async function main() {
  const server = new Server(
    {
      name: 'logging-mcp-server',
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
      case 'write_log':
        return handleWriteLog(args);
      case 'read_logs':
        return handleReadLogs(args);
      case 'get_audit_summary':
        return handleGetAuditSummary(args);
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
  console.error('Logging MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
