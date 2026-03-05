#!/usr/bin/env node
/**
 * Odoo 19 MCP Server
 * Connects Claude to Odoo via JSON-RPC API
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';
import http from 'http';
import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration from environment
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'ai_employee_db';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'admin';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'changeme123';

// Session storage
let sessionCookie = null;
let uid = null;

// Ensure directories exist
const logsDir = path.join(__dirname, 'Logs');
const accountingDir = path.join(__dirname, 'Accounting');

if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}
if (!fs.existsSync(accountingDir)) {
  fs.mkdirSync(accountingDir, { recursive: true });
}

// Logging utility
function logAction(action, details, result = null) {
  const logFile = path.join(logsDir, 'odoo_log.json');
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

// JSON-RPC client for Odoo
class OdooClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.cookie = null;
  }

  async jsonRpcRequest(endpoint, params) {
    return new Promise((resolve, reject) => {
      const url = new URL(endpoint, this.baseUrl);
      const payload = JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: params || {},
        id: Math.floor(Math.random() * 1000000)
      });

      const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === 'https:' ? 443 : 80),
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'Accept': 'application/json'
        }
      };

      if (this.cookie) {
        options.headers['Cookie'] = this.cookie;
      }

      const lib = url.protocol === 'https:' ? https : http;
      const req = lib.request(options, (res) => {
        let data = '';
        
        // Capture session cookie
        if (res.headers['set-cookie']) {
          const sessionCookies = res.headers['set-cookie'].filter(c => c.startsWith('session_id='));
          if (sessionCookies.length > 0) {
            this.cookie = sessionCookies.map(c => c.split(';')[0]).join('; ');
          }
        }

        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const response = JSON.parse(data);
            if (response.error) {
              reject(new Error(response.error.message || JSON.stringify(response.error)));
            } else {
              resolve(response.result);
            }
          } catch (e) {
            reject(new Error(`Failed to parse response: ${e.message}`));
          }
        });
      });

      req.on('error', reject);
      req.write(payload);
      req.end();
    });
  }

  async authenticate(db, username, password) {
    const result = await this.jsonRpcRequest('/web/session/authenticate', {
      db,
      login: username,
      password,
      context: {}
    });
    
    if (result && result.uid) {
      this.uid = result.uid;
      return result;
    }
    throw new Error('Authentication failed');
  }

  async execute(model, method, args = [], kwargs = {}) {
    return this.jsonRpcRequest('/web/dataset/call_kw', {
      model,
      method,
      args,
      kwargs: {
        ...kwargs,
        context: { ...kwargs.context, uid: this.uid }
      }
    });
  }

  async searchRead(model, domain, fields, limit = 80) {
    return this.execute(model, 'search_read', [domain, fields], { limit });
  }

  async create(model, values) {
    return this.execute(model, 'create', [values]);
  }

  async write(model, id, values) {
    return this.execute(model, 'write', [[id], values]);
  }
}

const client = new OdooClient(ODOO_URL);

// Tool definitions
const tools = [
  {
    name: 'odoo_get_invoices',
    description: 'Retrieve invoices from Odoo. Optionally filter by status (draft/posted/paid).',
    inputSchema: zodToJsonSchema(z.object({
      status: z.enum(['draft', 'posted', 'paid']).optional().describe('Filter by invoice status')
    }))
  },
  {
    name: 'odoo_create_invoice',
    description: 'Create a new DRAFT invoice in Odoo. Never posts automatically.',
    inputSchema: zodToJsonSchema(z.object({
      customer_name: z.string().describe('Customer/partner name'),
      amount: z.number().positive().describe('Invoice amount'),
      description: z.string().describe('Invoice line description'),
      due_date: z.string().describe('Due date in YYYY-MM-DD format')
    }))
  },
  {
    name: 'odoo_get_customers',
    description: 'Search for customers in Odoo. Optionally search by name.',
    inputSchema: zodToJsonSchema(z.object({
      search_name: z.string().optional().describe('Partial customer name to search')
    }))
  },
  {
    name: 'odoo_get_revenue_summary',
    description: 'Get revenue summary for a specific month and year.',
    inputSchema: zodToJsonSchema(z.object({
      month: z.number().min(1).max(12).describe('Month (1-12)'),
      year: z.number().min(2000).max(2100).describe('Year')
    }))
  },
  {
    name: 'odoo_flag_expense',
    description: 'Flag an expense for review by saving to flagged_expenses.md file.',
    inputSchema: zodToJsonSchema(z.object({
      description: z.string().describe('Expense description'),
      amount: z.number().positive().describe('Expense amount'),
      category: z.string().describe('Expense category')
    }))
  }
];

// Tool handlers
async function handleGetInvoices(args) {
  try {
    const domain = [];
    
    if (args.status) {
      const stateMap = {
        'draft': 'draft',
        'posted': 'posted',
        'paid': 'paid'
      };
      domain.push(['state', '=', stateMap[args.status]]);
    }

    const invoices = await client.searchRead(
      'account.move',
      domain,
      ['id', 'partner_id', 'invoice_date_due', 'amount_total', 'amount_residual', 'state', 'name'],
      100
    );

    const result = invoices.map(inv => ({
      id: inv.id,
      invoice_number: inv.name,
      client_name: inv.partner_id?.[1] || 'Unknown',
      amount: inv.amount_total,
      amount_due: inv.amount_residual,
      due_date: inv.invoice_date_due,
      status: inv.state
    }));

    logAction('get_invoices', { status: args.status || 'all' }, true);
    return {
      content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    logAction('get_invoices', { status: args.status, error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error fetching invoices: ${error.message}` }],
      isError: true
    };
  }
}

async function handleCreateInvoice(args) {
  try {
    // First, find or create the customer
    let partners = await client.searchRead(
      'res.partner',
      [['name', 'ilike', args.customer_name]],
      ['id', 'name'],
      10
    );

    let partnerId;
    if (partners.length > 0) {
      partnerId = partners[0].id;
    } else {
      // Create new partner
      partnerId = await client.create('res.partner', {
        name: args.customer_name
      });
    }

    // Create invoice in DRAFT state only - NEVER post automatically
    const invoiceId = await client.create('account.move', {
      move_type: 'out_invoice',
      partner_id: partnerId,
      invoice_date: new Date().toISOString().split('T')[0],
      invoice_date_due: args.due_date,
      invoice_line_ids: [
        [0, 0, {
          name: args.description,
          quantity: 1,
          price_unit: args.amount
        }]
      ]
    });

    logAction('create_invoice', { 
      customer_name: args.customer_name, 
      amount: args.amount,
      invoice_id: invoiceId 
    }, true);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          invoice_id: invoiceId,
          confirmation: `Draft invoice created successfully for ${args.customer_name}`,
          status: 'draft',
          note: 'Invoice created in DRAFT status. Manual review and posting required.'
        }, null, 2)
      }]
    };
  } catch (error) {
    logAction('create_invoice', { ...args, error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error creating invoice: ${error.message}` }],
      isError: true
    };
  }
}

async function handleGetCustomers(args) {
  try {
    const domain = args.search_name 
      ? [['name', 'ilike', args.search_name]]
      : [];

    const customers = await client.searchRead(
      'res.partner',
      domain,
      ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id'],
      50
    );

    const result = customers.map(cust => ({
      id: cust.id,
      name: cust.name,
      email: cust.email,
      phone: cust.phone,
      address: [cust.street, cust.city].filter(Boolean).join(', '),
      country: cust.country_id?.[1] || null
    }));

    logAction('get_customers', { search_name: args.search_name || 'all' }, true);
    return {
      content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    logAction('get_customers', { search_name: args.search_name, error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error fetching customers: ${error.message}` }],
      isError: true
    };
  }
}

async function handleGetRevenueSummary(args) {
  try {
    const { month, year } = args;
    
    // Calculate date range for the month
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0);
    
    const startDateStr = startDate.toISOString().split('T')[0];
    const endDateStr = endDate.toISOString().split('T')[0];

    // Get all invoices for the month
    const invoices = await client.searchRead(
      'account.move',
      [
        ['move_type', 'in', ['out_invoice', 'out_refund']],
        ['invoice_date', '>=', startDateStr],
        ['invoice_date', '<=', endDateStr],
        ['state', 'in', ['posted', 'paid']]
      ],
      ['id', 'amount_total', 'amount_residual', 'state', 'payment_state'],
      500
    );

    let totalInvoiced = 0;
    let totalPaid = 0;
    let totalOverdue = 0;
    const today = new Date().toISOString().split('T')[0];

    invoices.forEach(inv => {
      totalInvoiced += inv.amount_total;
      
      if (inv.payment_state === 'paid' || inv.state === 'paid') {
        totalPaid += inv.amount_total;
      } else if (inv.amount_residual > 0) {
        // Check if overdue (due date passed and not fully paid)
        if (inv.invoice_date_due && inv.invoice_date_due < today) {
          totalOverdue += inv.amount_residual;
        }
      }
    });

    const result = {
      month,
      year,
      total_invoiced: parseFloat(totalInvoiced.toFixed(2)),
      total_paid: parseFloat(totalPaid.toFixed(2)),
      total_overdue: parseFloat(totalOverdue.toFixed(2)),
      invoice_count: invoices.length
    };

    logAction('get_revenue_summary', { month, year }, true);
    return {
      content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
    };
  } catch (error) {
    logAction('get_revenue_summary', { ...args, error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error fetching revenue summary: ${error.message}` }],
      isError: true
    };
  }
}

async function handleFlagExpense(args) {
  try {
    const { description, amount, category } = args;
    const flaggedFile = path.join(accountingDir, 'flagged_expenses.md');
    
    // Read existing content or create header
    let content = '';
    if (fs.existsSync(flaggedFile)) {
      content = fs.readFileSync(flaggedFile, 'utf-8');
    } else {
      content = '# Flagged Expenses for Review\n\n';
      content += '| Date | Description | Amount | Category | Status |\n';
      content += '|------|-------------|--------|----------|--------|\n';
    }

    // Add new entry
    const date = new Date().toISOString().split('T')[0];
    const newEntry = `| ${date} | ${description} | $${amount.toFixed(2)} | ${category} | Pending Review |\n`;
    content += newEntry;

    fs.writeFileSync(flaggedFile, content);

    logAction('flag_expense', { description, amount, category }, true);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          confirmation: 'Expense flagged for review',
          details: {
            description,
            amount,
            category,
            flagged_at: date
          },
          file: './Accounting/flagged_expenses.md'
        }, null, 2)
      }]
    };
  } catch (error) {
    logAction('flag_expense', { ...args, error: error.message }, false);
    return {
      content: [{ type: 'text', text: `Error flagging expense: ${error.message}` }],
      isError: true
    };
  }
}

// Main server setup
async function main() {
  // Authenticate with Odoo
  try {
    console.error('Authenticating with Odoo...');
    await client.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD);
    console.error(`Authenticated successfully. User ID: ${client.uid}`);
    logAction('authentication', { username: ODOO_USERNAME, url: ODOO_URL }, true);
  } catch (error) {
    console.error(`Authentication failed: ${error.message}`);
    logAction('authentication', { username: ODOO_USERNAME, error: error.message }, false);
    process.exit(1);
  }

  const server = new Server(
    {
      name: 'odoo-mcp-server',
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
      case 'odoo_get_invoices':
        return handleGetInvoices(args);
      case 'odoo_create_invoice':
        return handleCreateInvoice(args);
      case 'odoo_get_customers':
        return handleGetCustomers(args);
      case 'odoo_get_revenue_summary':
        return handleGetRevenueSummary(args);
      case 'odoo_flag_expense':
        return handleFlagExpense(args);
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
  console.error('Odoo MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
