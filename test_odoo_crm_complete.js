/**
 * Odoo CRM - Complete Test Suite
 * Tests all CRM functionalities
 */

import xmlrpc from 'xmlrpc';
import dotenv from 'dotenv';

dotenv.config();

// Configuration
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const ODOO_DB = process.env.ODOO_DB || 'ai_employee_db';
const ODOO_USERNAME = process.env.ODOO_USERNAME || 'ma9400667@gmail.com';
const ODOO_PASSWORD = process.env.ODOO_PASSWORD || 'Admin@123';

console.log('=== Odoo CRM Complete Test Suite ===\n');
console.log(`URL: ${ODOO_URL}`);
console.log(`Database: ${ODOO_DB}`);
console.log(`Username: ${ODOO_USERNAME}\n`);

// Parse URL
const url = new URL(ODOO_URL);
const hostname = url.hostname;
const port = url.port || (url.protocol === 'https:' ? 443 : 80);

// Create clients
const commonClient = xmlrpc.createClient({
    host: hostname,
    port: parseInt(port),
    path: '/xmlrpc/2/common',
});

const objectClient = xmlrpc.createClient({
    host: hostname,
    port: parseInt(port),
    path: '/xmlrpc/2/object',
});

let uid = null;

// Authenticate
function authenticate() {
    return new Promise((resolve, reject) => {
        console.log('1. Authenticating...');
        commonClient.methodCall('authenticate', [ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {}], (error, result) => {
            if (error) {
                reject(error);
                return;
            }
            if (!result) {
                reject(new Error('Authentication failed'));
                return;
            }
            uid = result;
            console.log(`   ✓ Authentication successful! (UID: ${uid})\n`);
            resolve(uid);
        });
    });
}

// Test 1: Get Customers
async function testGetCustomers() {
    console.log('2. Testing: Get Customers');
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner',
            'search_read',
            [[['customer_rank', '>', 0]]],
            { fields: ['name', 'email', 'phone', 'street', 'city', 'zip'] }
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Found ${result.length} customers:`);
            result.forEach((c, i) => {
                console.log(`   ${i+1}. ${c.name}`);
                console.log(`      Email: ${c.email || 'N/A'}`);
                console.log(`      Phone: ${c.phone || 'N/A'}`);
                console.log(`      Location: ${c.city || 'N/A'}, ${c.zip || 'N/A'}`);
            });
            console.log('');
            resolve(result);
        });
    });
}

// Test 2: Create New Customer
async function testCreateCustomer() {
    console.log('3. Testing: Create New Customer');
    
    const newCustomer = {
        name: 'Test CRM Customer ' + Date.now(),
        email: `testcrm${Date.now()}@test.com`,
        phone: '+1-555-9999',
        customer_rank: 1,
        street: '123 CRM Test Street',
        city: 'Test City',
        zip: '12345'
        // Removed country_id - causes issues
    };
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner',
            'create',
            [[newCustomer]]
        ], (error, customerId) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Customer created! (ID: ${customerId})`);
            console.log(`      Name: ${newCustomer.name}`);
            console.log(`      Email: ${newCustomer.email}\n`);
            resolve(customerId);
        });
    });
}

// Test 3: Get Invoices
async function testGetInvoices() {
    console.log('4. Testing: Get Invoices');
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move',
            'search_read',
            [[]],
            { 
                fields: ['name', 'partner_id', 'amount_total', 'state', 'invoice_date', 'move_type'],
                limit: 10
            }
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Found ${result.length} recent invoices:`);
            result.forEach((inv, i) => {
                const customer = inv.partner_id ? inv.partner_id[1] : 'Unknown';
                const type = inv.move_type === 'out_invoice' ? 'Customer Invoice' : 
                            inv.move_type === 'in_invoice' ? 'Vendor Bill' : inv.move_type;
                console.log(`   ${i+1}. ${inv.name || 'Draft'} - $${inv.amount_total} (${inv.state}) - ${customer}`);
            });
            console.log('');
            resolve(result);
        });
    });
}

// Test 4: Create Invoice
async function testCreateInvoice(customerId) {
    console.log('5. Testing: Create Customer Invoice');
    
    if (!customerId) {
        console.log('   ⚠ Skipping - No customer ID\n');
        return null;
    }
    
    const invoiceData = {
        move_type: 'out_invoice',
        partner_id: customerId,
        invoice_line_ids: [[0, 0, {
            name: 'CRM Testing Services',
            quantity: 2,
            price_unit: 250
        }]],
        invoice_date: new Date().toISOString().split('T')[0]
    };
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move',
            'create',
            [[invoiceData]]
        ], (error, invoiceId) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Invoice created! (ID: ${invoiceId})`);
            console.log(`      Customer ID: ${customerId}`);
            console.log(`      Amount: $500 (2 x $250)\n`);
            
            // Post the invoice
            console.log('   Posting invoice...');
            objectClient.methodCall('execute_kw', [
                ODOO_DB, uid, ODOO_PASSWORD,
                'account.move',
                'action_post',
                [[invoiceId]]
            ], (postError) => {
                if (postError) {
                    console.log(`   ⚠ Could not auto-post: ${postError.message}`);
                } else {
                    console.log('   ✓ Invoice posted successfully!');
                }
                console.log('');
                resolve(invoiceId);
            });
        });
    });
}

// Test 5: Get Revenue Summary
async function testGetRevenueSummary() {
    console.log('6. Testing: Get Revenue Summary');
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move',
            'search_read',
            [[['move_type', '=', 'out_invoice']]],
            { fields: ['amount_total', 'state'] }
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            let total = 0;
            let posted = 0;
            let draft = 0;
            
            result.forEach(inv => {
                total += inv.amount_total || 0;
                if (inv.state === 'posted') posted++;
                if (inv.state === 'draft') draft++;
            });
            
            console.log(`   ✓ Revenue Summary:`);
            console.log(`      Total Invoices: ${result.length}`);
            console.log(`      Total Revenue: $${total.toLocaleString('en-US', {minimumFractionDigits: 2})}`);
            console.log(`      Posted: ${posted}`);
            console.log(`      Draft: ${draft}\n`);
            resolve({ total, count: result.length, posted, draft });
        });
    });
}

// Test 6: Search Customer by Email
async function testSearchCustomer() {
    console.log('7. Testing: Search Customer by Email');
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner',
            'search_read',
            [[['email', 'ilike', 'acme']]],
            { fields: ['name', 'email', 'phone'] }
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Found ${result.length} customers matching "acme":`);
            result.forEach((c, i) => {
                console.log(`   ${i+1}. ${c.name} - ${c.email}`);
            });
            console.log('');
            resolve(result);
        });
    });
}

// Test 7: Update Customer
async function testUpdateCustomer(customerId) {
    console.log('8. Testing: Update Customer');
    
    if (!customerId) {
        console.log('   ⚠ Skipping - No customer ID\n');
        return null;
    }
    
    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner',
            'write',
            [[customerId], {
                phone: '+1-555-UPDATED',
                street: 'Updated Address 123'
            }]
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            console.log(`   ✓ Customer ${customerId} updated successfully!`);
            console.log(`      New Phone: +1-555-UPDATED\n`);
            resolve(result);
        });
    });
}

// Test 8: Get Top Customers by Revenue
async function testGetTopCustomers() {
    console.log('9. Testing: Get Top Customers by Revenue');

    return new Promise((resolve) => {
        objectClient.methodCall('execute_kw', [
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move',
            'search_read',
            [[['move_type', '=', 'out_invoice'], ['state', '=', 'posted']]],
            { fields: ['partner_id', 'amount_total'] }
        ], (error, result) => {
            if (error) {
                console.log(`   ✗ Error: ${error.message}\n`);
                resolve(null);
                return;
            }
            
            // Group by customer
            const customerRevenue = {};
            result.forEach(inv => {
                if (inv.partner_id) {
                    const customerName = inv.partner_id[1];
                    if (!customerRevenue[customerName]) {
                        customerRevenue[customerName] = 0;
                    }
                    customerRevenue[customerName] += inv.amount_total || 0;
                }
            });
            
            // Sort by revenue
            const sorted = Object.entries(customerRevenue)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5);
            
            console.log('   ✓ Top 5 Customers by Revenue:');
            sorted.forEach((c, i) => {
                console.log(`   ${i+1}. ${c[0]}: $${c[1].toLocaleString('en-US', {minimumFractionDigits: 2})}`);
            });
            console.log('');
            resolve(sorted);
        });
    });
}

// Test 9: Flag Expense (for review)
async function testFlagExpense() {
    console.log('10. Testing: Flag Expense for Review');
    
    // Skip this test - requires valid vendor ID
    console.log('   ⚠ Skipping - Requires valid vendor setup\n');
    return null;
}

// Generate Final Report
function generateReport(results) {
    console.log('=== CRM TEST SUMMARY ===\n');
    
    const passed = results.filter(r => r).length;
    const total = results.length;
    
    console.log(`Tests Completed: ${passed}/${total}`);
    console.log(`Success Rate: ${((passed/total)*100).toFixed(1)}%`);
    
    if (passed === total) {
        console.log('\n✅ ALL CRM TESTS PASSED!');
        console.log('Odoo CRM is fully functional and ready for production!\n');
    } else {
        console.log('\n⚠ Some tests did not complete. Review errors above.\n');
    }
}

// Main execution
async function runAllTests() {
    try {
        await authenticate();
        
        const results = [];
        
        // Run all tests
        results.push(await testGetCustomers());
        results.push(await testCreateCustomer());
        results.push(await testGetInvoices());
        
        const newCustomerId = await testCreateCustomer();
        results.push(newCustomerId);
        
        results.push(await testCreateInvoice(newCustomerId));
        results.push(await testGetRevenueSummary());
        results.push(await testSearchCustomer());
        results.push(await testUpdateCustomer(newCustomerId));
        results.push(await testGetTopCustomers());
        results.push(await testFlagExpense());
        
        // Generate report
        generateReport(results);
        
    } catch (error) {
        console.error(`\n✗ Test suite failed: ${error.message}`);
        console.error('Make sure Odoo is running: docker compose ps\n');
        process.exit(1);
    }
}

// Run tests
runAllTests();
