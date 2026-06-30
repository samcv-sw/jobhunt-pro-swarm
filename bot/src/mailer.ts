import nodemailer from 'nodemailer';
import fs from 'fs';
import path from 'path';

export function getRandomEmailAccount(): any {
    const accountsJson = process.env.GMAIL_ACCOUNTS_JSON;
    if (!accountsJson) {
        console.warn("WARNING: GMAIL_ACCOUNTS_JSON not set.");
        return null;
    }
    
    try {
        const accounts = JSON.parse(accountsJson);
        if (accounts && accounts.length > 0) {
            return accounts[Math.floor(Math.random() * accounts.length)];
        }
    } catch (e) {
        console.error("Error parsing GMAIL_ACCOUNTS_JSON:", e);
    }
    return null;
}

export async function sendColdEmail(toEmail: string, subject: string, htmlBody: string): Promise<boolean> {
    const account = getRandomEmailAccount();
    if (!account) {
        console.error("❌ No email account available for sending.");
        return false;
    }

    console.log(`📧 Sending Cold Pitch to ${toEmail} using ${account.email}...`);

    try {
        // Determine host based on email domain
        let host = 'smtp.gmail.com';
        if (account.email.toLowerCase().includes('hotmail') || account.email.toLowerCase().includes('outlook')) {
            host = 'smtp-mail.outlook.com';
        }

        const transporter = nodemailer.createTransport({
            host: host,
            port: 587,
            secure: false, // true for 465, false for other ports
            auth: {
                user: account.email,
                pass: account.password,
            },
        });

        const attachments = [];
        const cvPath = path.join(process.cwd(), '..', 'assets', 'Sam_Salameh_CV.pdf'); // bot/../assets
        if (fs.existsSync(cvPath)) {
            attachments.push({
                filename: 'Sam_Salameh_CV.pdf',
                path: cvPath
            });
            console.log(`📎 Attached CV: ${cvPath}`);
        } else {
            console.warn(`⚠️ CV file not found at ${cvPath}. Sending email without attachment.`);
        }

        const info = await transporter.sendMail({
            from: `"JobHunt Pro" <${account.email}>`,
            to: toEmail,
            subject: subject,
            html: htmlBody,
            attachments: attachments
        });

        console.log(`✅ Email sent successfully! Message ID: ${info.messageId}`);
        return true;
    } catch (err) {
        console.error("❌ Failed to send email:", err);
        return false;
    }
}
