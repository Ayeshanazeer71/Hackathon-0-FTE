/**
 * Odoo Test Script - XML-RPC API
 * Tests Odoo connection using standard XML-RPC API
 */

import xmlrpc from 'xmlrpc';
import dotenv from 'dotenv';

dotenv.config();

// Configuration
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'ai_employee_db';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'ma9400667@gmail.com';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'Admin@123';

console.log('=== Odoo XML-RPC Test ===\n');
console.log(`URL: ${ODOO_URL}`);
console.log(`Database: ${ODOO_DB}`);
console.log(`Username: ${ODOO_USERNAME}\n`);

// Parse URL
const url = new URL(ODOO_URL);
const hostname = url.hostname;
const port = url.port || (url.protocol === 'https:' ? 443 : 80);
const protocol = url.protocol === 'https:' ? 'https' : 'http';

// Create client
const client = xmlrpc.createClient({
    host: hostname,
    port: parseInt(port),
    path: '/xmlrpc/2/common',
});

const objectClient = xmlrpc.createClient({
    host: hostname,
    port: parseInt(port),
    path: '/xmlrpc/2/object',
});

// Authenticate
function authenticate() {
    return new Promise((resolve, reject) => {
        console.log('Authenticating...');
        
        client.methodCall('authenticate', [ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {}], (error, uid) => {
            if (error) {
                reject(error);
                return;
            }
            
            if (!uid) {
                reject(new Error('Authentication failed - check credentials'));
                return;
            }
            
            console.log(`✓ Authentication successful! (UID: ${uid})\n`);
            resolve(uid);
        });
    });
}

// Get customers
async function getCustomers(uid) {
    console.log('Getting customers...');
    
    return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'res.partner',
            'search_read',
            [[['customer_rank', '>', 0]]],
            { fields: ['name', 'email', 'phone', 'customer_rank'] }
        ], (error, result) => {
            if (error) {
                console.log(`✗ Error: ${error.message}`);
                resolve([]);
                return;
            }
            
            if (result && result.length > 0) {
                console.log(`✓ Found ${result.length} customers:`);
                result.forEach(c => {
                    console.log(`  - ${c.name} (${c.email || 'no email'}) - ${c.phone || 'no phone'}`);
                });
            } else {
                console.log('  No customers found');
            }
            
            resolve(result);
        });
    });
}

// Get invoices
async function getInvoices(uid) {
    console.log('\nGetting invoices...');
    
    return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'account.move',
            'search_read',
            [[]],
            { fields: ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'] }
        ], (error, result) => {
            if (error) {
                console.log(`✗ Error: ${error.message}`);
                console.log('Note: Invoicing module may not be installed');
                resolve([]);
                return;
            }
            
            if (result && result.length > 0) {
                console.log(`✓ Found ${result.length} invoices:`);
                result.forEach(inv => {
                    const customer = inv.partner_id ? inv.partner_id[1] : 'Unknown';
                    console.log(`  - ${inv.name}: $${inv.amount_total} (${inv.state}) - ${customer}`);
                });
            } else {
                console.log('  No invoices found');
            }
            
            resolve(result);
        });
    });
}

// Get installed modules
async function getModules(uid) {
    console.log('\nGetting installed modules...');
    
    return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'ir.module.module',
            'search_read',
            [[['state', '=', 'installed']]],
            { fields: ['name', 'summary'], limit: 15 }
        ], (error, result) => {
            if (error) {
                console.log(`✗ Error: ${error.message}`);
                resolve([]);
                return;
            }
            
            if (result && result.length > 0) {
                console.log(`✓ Found ${result.length} installed modules:`);
                result.forEach(m => {
                    console.log(`  - ${m.name}`);
                });
                
                // Check for accounting
                const hasAccount = result.some(m => m.name.includes('account'));
                if (!hasAccount) {
                    console.log('\n⚠️  Invoicing module not installed!');
                    console.log('Install from: Apps → Search "Invoicing" → Install');
                }
            } else {
                console.log('  No modules found');
            }
            
            resolve(result);
        });
    });
}

// Create test customer
async function createCustomer(uid) {
    console.log('\nCreating test customer...');
    
    return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'res.partner',
            'create',
            [[{
                name: 'Test Client A',
                email: 'contact@testclienta.com',
                phone: '+1-555-0123',
                customer_rank: 1
            }]]
        ], (error, result) => {
            if (error) {
                console.log(`✗ Error: ${error.message}`);
                resolve(null);
                return;
            }
            
            console.log(`✓ Customer created! (ID: ${result})`);
            resolve(result);
        });
    });
}

// Create test invoice
async function createInvoice(uid, customerId) {
    console.log('\nCreating test invoice ($500)...');
    
    return new Promise((resolve, reject) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'account.move',
            'create',
            [[{
                move_type: 'out_invoice',
                partner_id: customerId,
                invoice_line_ids: [[0, 0, {
                    name: 'Consulting Services',
                    quantity: 1,
                    price_unit: 500
                }]]
            }]]
        ], (error, invoiceId) => {
            if (error) {
                console.log(`✗ Error creating invoice: ${error.message}`);
                resolve(null);
                return;
            }
            
            console.log(`✓ Invoice created! (ID: ${invoiceId})`);
            
            // Post invoice
            console.log('Posting invoice...');
            objectClient.methodCall('execute_kw', [
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'account.move',
                'action_post',
                [[invoiceId]]
            ], (postError) => {
                if (postError) {
                    console.log(`⚠️  Could not auto-post: ${postError.message}`);
                } else {
                    console.log('✓ Invoice posted!');
                }
                resolve(invoiceId);
            });
        });
    });
}

// Main
async function run() {
    try {
        const uid = await authenticate();
        
        await getModules(uid);
        await getCustomers(uid);
        await getInvoices(uid);
        
        // Ask if user wants to create test data
        console.log('\n=== Summary ===');
        console.log('✓ Odoo is running');
        console.log('✓ Authentication successful');
        console.log(`Database: ${ODOO_DB}`);
        console.log(`User: ${ODOO_USERNAME}`);
        
    } catch (error) {
        console.error(`\n✗ Test failed: ${error.message}`);
        console.log('\nMake sure:');
        console.log('  1. Odoo is running: docker compose ps');
        console.log('  2. Credentials are correct in .env file');
        console.log('  3. Database exists: http://localhost:8069');
    }
}

run();
