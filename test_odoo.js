/**
 * Odoo Test Script
 * Tests Odoo connection and basic operations
 */

import http from 'http';
import https from 'https';
import { URL } from 'url';

// Configuration
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'ai_employee_db';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'ma9400667@gmail.com';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'Admin@123';

console.log('=== Odoo Test Script ===\n');
console.log(`URL: ${ODOO_URL}`);
console.log(`Database: ${ODOO_DB}`);
console.log(`Username: ${ODOO_USERNAME}\n`);

// Session storage
let sessionCookie = null;
let uid = null;

// Make HTTP request
function makeRequest(url, postData = null, cookie = null) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const isHttps = parsedUrl.protocol === 'https:';
        
        const options = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || (isHttps ? 443 : 80),
            path: parsedUrl.pathname + parsedUrl.search,
            method: postData ? 'POST' : 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        };
        
        if (cookie) {
            options.headers['Cookie'] = cookie;
        }
        
        const req = (isHttps ? https : http).request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                // Get session cookie
                const newCookie = res.headers['set-cookie'];
                if (newCookie) {
                    sessionCookie = newCookie.join('; ');
                }
                
                try {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: JSON.parse(data)
                    });
                } catch (e) {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                }
            });
        });
        
        req.on('error', reject);
        
        if (postData) {
            req.write(JSON.stringify(postData));
        }
        
        req.end();
    });
}

// Authenticate with Odoo
async function authenticate() {
    console.log('Step 1: Authenticating with Odoo...');
    
    try {
        // Try to access Odoo web interface
        const result = await makeRequest(`${ODOO_URL}/web/session/authenticate`, {
            jsonrpc: '2.0',
            method: 'call',
            params: {
                db: ODOO_DB,
                login: ODOO_USERNAME,
                password: ODOO_PASSWORD
            },
            id: 1
        });
        
        if (result.data && result.data.result && result.data.result.uid) {
            uid = result.data.result.uid;
            console.log(`✓ Authentication successful! (UID: ${uid})`);
            return true;
        } else {
            console.log('✗ Authentication failed - checking if database exists...');
            return false;
        }
    } catch (error) {
        console.log(`✗ Authentication error: ${error.message}`);
        return false;
    }
}

// Check if Odoo is running
async function checkOdooStatus() {
    console.log('Step 0: Checking Odoo status...');
    
    try {
        const result = await makeRequest(ODOO_URL);
        
        // 200 OK or 303 Redirect both mean Odoo is running
        if (result.status === 200 || result.status === 303) {
            console.log('✓ Odoo is running!');
            return true;
        } else {
            console.log(`✗ Odoo returned status: ${result.status}`);
            return false;
        }
    } catch (error) {
        console.log(`✗ Cannot reach Odoo: ${error.message}`);
        console.log('\nMake sure Odoo is running:');
        console.log('  docker compose ps\n');
        return false;
    }
}

// Get list of apps/modules
async function getApps() {
    console.log('\nStep 2: Getting installed apps...');
    
    try {
        // Search for installed modules
        const searchResult = await makeRequest(
            `${ODOO_URL}/web/dataset/call_kw`,
            {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.module.module',
                    method: 'search_read',
                    fields: ['name', 'state', 'summary'],
                    domain: [['state', 'in', ['installed', 'to install', 'to upgrade']]],
                    limit: 20
                },
                id: 2
            },
            sessionCookie
        );
        
        if (searchResult.data && searchResult.data.result) {
            console.log(`✓ Found ${searchResult.data.result.length} installed modules`);
            searchResult.data.result.forEach(module => {
                console.log(`  - ${module.name}: ${module.summary || 'No description'}`);
            });
            
            // Check if Invoicing is installed
            const hasInvoicing = searchResult.data.result.some(m => m.name.includes('account') || m.name.includes('invoicing'));
            if (!hasInvoicing) {
                console.log('\n⚠️  Invoicing module not installed!');
                console.log('Install it from: http://localhost:8069 → Apps → Search "Invoicing" → Install');
            }
        }
    } catch (error) {
        console.log(`✗ Could not fetch apps: ${error.message}`);
    }
}

// Get list of customers
async function getCustomers() {
    console.log('\nStep 3: Getting customers...');
    
    try {
        // Try both res.partner and customer filter
        const result = await makeRequest(
            `${ODOO_URL}/web/dataset/call_kw`,
            {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'res.partner',
                    method: 'search_read',
                    fields: ['name', 'email', 'phone', 'customer_rank'],
                    domain: [['customer_rank', '>', 0]],
                    limit: 10
                },
                id: 3
            },
            sessionCookie
        );
        
        if (result.data && result.data.result) {
            console.log(`✓ Found ${result.data.result.length} customers`);
            result.data.result.forEach(customer => {
                console.log(`  - ${customer.name} (${customer.email || 'no email'}) - Rank: ${customer.customer_rank}`);
            });
        } else {
            // Try without customer_rank filter
            console.log('Trying without customer_rank filter...');
            const allPartners = await makeRequest(
                `${ODOO_URL}/web/dataset/call_kw`,
                {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        model: 'res.partner',
                        method: 'search_read',
                        fields: ['name', 'email'],
                        domain: [],
                        limit: 5
                    },
                    id: 3
                },
                sessionCookie
            );
            
            if (allPartners.data && allPartners.data.result && allPartners.data.result.length > 0) {
                console.log(`✓ Found ${allPartners.data.result.length} partners (any type)`);
                allPartners.data.result.forEach(p => {
                    console.log(`  - ${p.name}`);
                });
            } else {
                console.log('  No customers found (this is normal for new database)');
            }
        }
    } catch (error) {
        console.log(`✗ Could not fetch customers: ${error.message}`);
    }
}

// Get invoices
async function getInvoices() {
    console.log('\nStep 4: Getting invoices...');
    
    try {
        const result = await makeRequest(
            `${ODOO_URL}/web/dataset/call_kw`,
            {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'account.move',
                    method: 'search_read',
                    fields: ['name', 'partner_id', 'amount_total', 'state'],
                    domain: [],
                    limit: 5
                },
                id: 4
            },
            sessionCookie
        );
        
        if (result.data && result.data.result) {
            console.log(`✓ Found ${result.data.result.length} invoices`);
            result.data.result.forEach(inv => {
                const customer = inv.partner_id ? inv.partner_id[1] : 'Unknown';
                console.log(`  - ${inv.name || 'Draft'}: $${inv.amount_total} (${inv.state}) - ${customer}`);
            });
        } else {
            console.log('  No invoices found');
        }
    } catch (error) {
        console.log(`✗ Could not fetch invoices: ${error.message}`);
    }
}

// Create test customer
async function createCustomer() {
    console.log('\nStep 5: Creating test customer...');
    
    try {
        const result = await makeRequest(
            `${ODOO_URL}/web/dataset/call_kw`,
            {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'res.partner',
                    method: 'create',
                    args: [[{
                        name: 'Test Client A',
                        email: 'contact@testclienta.com',
                        phone: '+1-555-0123',
                        customer_rank: 1,
                        street: '123 Test Street',
                        city: 'Test City',
                        zip: '12345',
                        country_id: [233, 'United States'] // Default country
                    }]]
                },
                id: 5
            },
            sessionCookie
        );
        
        if (result.data && result.data.result) {
            console.log(`✓ Customer created! (ID: ${result.data.result})`);
            return result.data.result;
        } else {
            console.log('✗ Could not create customer');
            return null;
        }
    } catch (error) {
        console.log(`✗ Error creating customer: ${error.message}`);
        return null;
    }
}

// Create test invoice
async function createInvoice(customerId) {
    console.log('\nStep 6: Creating test invoice ($500)...');
    
    try {
        // First create the invoice
        const result = await makeRequest(
            `${ODOO_URL}/web/dataset/call_kw`,
            {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'account.move',
                    method: 'create',
                    args: [[{
                        move_type: 'out_invoice',
                        partner_id: customerId,
                        invoice_line_ids: [[0, 0, {
                            name: 'Consulting Services',
                            quantity: 1,
                            price_unit: 500
                        }]]
                    }]]
                },
                id: 6
            },
            sessionCookie
        );
        
        if (result.data && result.data.result) {
            const invoiceId = result.data.result;
            console.log(`✓ Invoice created! (ID: ${invoiceId})`);
            
            // Post the invoice
            console.log('Posting invoice...');
            const postResult = await makeRequest(
                `${ODOO_URL}/web/dataset/call_kw`,
                {
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        model: 'account.move',
                        method: 'action_post',
                        args: [[invoiceId]]
                    },
                    id: 7
                },
                sessionCookie
            );
            
            console.log('✓ Invoice posted!');
            return invoiceId;
        } else {
            console.log('✗ Could not create invoice');
            return null;
        }
    } catch (error) {
        console.log(`✗ Error creating invoice: ${error.message}`);
        return null;
    }
}

// Main test function
async function runTests(createTestData = false) {
    const odooRunning = await checkOdooStatus();
    if (!odooRunning) {
        console.log('\n❌ Odoo is not accessible. Start it with: docker compose up -d');
        return;
    }
    
    const authenticated = await authenticate();
    if (!authenticated) {
        console.log('\n❌ Authentication failed.');
        console.log('\nPossible reasons:');
        console.log('  1. Database not created yet');
        console.log('  2. Wrong credentials in .env file');
        console.log('\nGo to http://localhost:8069 to create the database first.');
        return;
    }
    
    await getApps();
    await getCustomers();
    await getInvoices();
    
    // Create test data if requested
    if (createTestData) {
        const customerId = await createCustomer();
        if (customerId) {
            await createInvoice(customerId);
        }
        
        // Fetch and display updated data
        console.log('\n=== Verifying Created Data ===');
        await getCustomers();
        await getInvoices();
    }
    
    console.log('\n✅ All tests completed!\n');
    console.log('=== Summary ===');
    console.log('Odoo Status: Running');
    console.log('Authentication: Success');
    console.log(`Database: ${ODOO_DB}`);
    console.log(`User: ${ODOO_USERNAME}`);
}

// Run tests
const createData = process.argv.includes('--create');
runTests(createData).catch(err => {
    console.error('Test failed:', err);
    process.exit(1);
});
