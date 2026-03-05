#!/usr/bin/env node
/**
 * Test Email Configuration
 * Verifies Gmail credentials and sends a test email
 */

import { config } from 'dotenv';
import nodemailer from 'nodemailer';

// Load .env file
config();

console.log('='.repeat(60));
console.log('       EMAIL CONFIGURATION TEST');
console.log('='.repeat(60));

// Check environment variables
const gmailUser = process.env.GMAIL_USER;
const gmailPassword = process.env.GMAIL_APP_PASSWORD;

console.log('\n[1] Checking Environment Variables...\n');

if (!gmailUser) {
    console.log('❌ GMAIL_USER: NOT SET');
    process.exit(1);
} else {
    console.log(`✅ GMAIL_USER: ${gmailUser}`);
}

if (!gmailPassword) {
    console.log('❌ GMAIL_APP_PASSWORD: NOT SET');
    process.exit(1);
} else {
    const masked = gmailPassword.replace(/./g, '*').substring(0, 8) + '****';
    console.log(`✅ GMAIL_APP_PASSWORD: ${masked}`);
}

console.log('\n[2] Creating Gmail Transporter...\n');

try {
    const transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: gmailUser,
            pass: gmailPassword
        }
    });

    console.log('✅ Transporter created successfully');

    // Verify connection
    console.log('\n[3] Verifying Gmail Connection...\n');
    
    transporter.verify(function(error, success) {
        if (error) {
            console.log('❌ Connection Failed!');
            console.log(`Error: ${error.message}`);
            console.log('\n[TROUBLESHOOTING]');
            console.log('1. Check if App Password is correct (16 characters)');
            console.log('2. Remove spaces from password: "abcd efgh ijkl mnop" → "abcdefghijklmnop"');
            console.log('3. Ensure 2-Step Verification is enabled on Gmail');
            console.log('4. Generate a new App Password: https://myaccount.google.com/apppasswords');
            process.exit(1);
        } else {
            console.log('✅ Gmail Connection Verified!');
            console.log('✅ Server is ready to send mails');
            
            console.log('\n[4] Sending Test Email...\n');
            
            // Send test email to self
            const mailOptions = {
                from: gmailUser,
                to: gmailUser,
                subject: 'Email MCP Test - Success!',
                text: `This is a test email from your Email MCP Server.\n\nIf you received this, your Gmail configuration is working correctly!\n\nTimestamp: ${new Date().toISOString()}\nFrom: Email MCP Server`,
                html: `<h2>Email MCP Test - Success!</h2><p>This is a test email from your <strong>Email MCP Server</strong>.</p><p>If you received this, your Gmail configuration is working correctly!</p><p><strong>Timestamp:</strong> ${new Date().toISOString()}<br><strong>From:</strong> Email MCP Server</p>`
            };
            
            transporter.sendMail(mailOptions, function(error, info) {
                if (error) {
                    console.log('❌ Test Email Failed!');
                    console.log(`Error: ${error.message}`);
                    process.exit(1);
                } else {
                    console.log('✅ Test Email Sent Successfully!');
                    console.log(`Message ID: ${info.messageId}`);
                    console.log('\n' + '='.repeat(60));
                    console.log('       ALL TESTS PASSED! ✅');
                    console.log('='.repeat(60));
                    console.log('\nYour Email MCP Server is ready to use!');
                    console.log(`Check your inbox at ${gmailUser} for the test email.`);
                }
            });
        }
    });

} catch (error) {
    console.log('❌ Error creating transporter');
    console.log(`Error: ${error.message}`);
    process.exit(1);
}
