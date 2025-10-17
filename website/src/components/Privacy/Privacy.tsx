import React from 'react';
import './Privacy.css';

const Privacy: React.FC = () => {
  return (
    <div className="privacy-container">
      <div className="privacy-content">
        <h1>Privacy Policy</h1>
        
        <p><strong>Effective Date:</strong> 1 Oct, 2025</p>
        <p><strong>Last Updated:</strong> 16 Oct, 2025</p>
        
        <p>Welcome to <strong>Superagent.diy</strong> ("we", "our", or "us"). Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your personal information when you use our service.</p>
        
        <hr />
        
        <h2>1. Information We Collect</h2>
        
        <p>When you use Superagent, we may collect the following types of personal information:</p>
        
        <ul>
          <li><strong>Name</strong></li>
          <li><strong>Email address</strong></li>
          <li><strong>Google Calendar data</strong> (such as event titles, times, descriptions, and associated metadata)</li>
        </ul>
        
        <p>This information is collected when you authenticate and connect your Google Calendar account.</p>
        
        <hr />
        
        <h2>2. How We Use Your Information</h2>
        
        <p>We use your information strictly to:</p>
        
        <ul>
          <li>Provide and operate the Superagent service</li>
          <li>Manage your calendar via Google Calendar API</li>
          <li>Respond to your commands and queries related to your calendar</li>
        </ul>
        
        <p>We <strong>do not</strong> use your data for advertising or share it with third parties for marketing purposes.</p>
        
        <hr />
        
        <h2>3. Data Storage and Security</h2>
        
        <p>All collected information is stored securely on our servers. We implement industry-standard security measures to protect your personal data from unauthorized access, disclosure, or destruction.</p>
        
        <p>However, no method of transmission over the Internet or method of electronic storage is 100% secure. Therefore, while we strive to use commercially acceptable means to protect your data, we cannot guarantee its absolute security.</p>
        
        <hr />
        
        <h2>4. Google API Disclosure</h2>
        
        <p>Superagent's use of information received from Google APIs adheres to the <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>
        
        <hr />
        
        <h2>5. Data Retention</h2>
        
        <p>We retain your personal data for as long as necessary to provide our services, or until you request deletion. If you disconnect your Google account or stop using Superagent, you may contact us to request the removal of your data.</p>
        
        <hr />
        
        <h2>6. User Control & Deletion</h2>
        
        <p>You may:</p>
        
        <ul>
          <li>Revoke access via your Google Account permissions</li>
          <li>Contact us to request deletion of your personal information from our servers</li>
        </ul>
        
        <p>Please email support[at]superagent.diy for any data deletion requests.</p>
        
        <hr />
        
        <h2>7. Changes to This Privacy Policy</h2>
        
        <p>We may update this policy from time to time. If we make significant changes, we will notify you via email or a notice on the site.</p>
        
        <hr />
        
        <h2>8. Contact Us</h2>
        
        <p>If you have questions about this policy, contact us at:</p>
        
        <p><strong>Email:</strong> support[at]superagent.diy<br />
        <strong>Website:</strong> https://superagent.diy</p>
      </div>
    </div>
  );
};

export default Privacy;
