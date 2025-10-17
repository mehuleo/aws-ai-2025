import React from 'react';
import './Terms.css';

const Terms: React.FC = () => {
  return (
    <div className="terms-container">
      <div className="terms-content">
        <h1>Terms and Conditions</h1>
        
        <p><strong>Effective Date:</strong> 1 Oct, 2025</p>
        <p><strong>Last Updated:</strong> 16 Oct, 2025</p>
        
        <p>Welcome to <strong>Superagent.diy</strong> ("Superagent", "we", "our", or "us"). By accessing or using our web application, you agree to be bound by the following terms and conditions ("Terms"). If you do not agree with these Terms, please do not use the Service.</p>
        
        <hr />
        
        <h2>1. Service Description</h2>
        
        <p>Superagent is a productivity tool that connects with your Google Calendar and allows you to manage your schedule via AI-driven natural language interactions.</p>
        
        <hr />
        
        <h2>2. Eligibility</h2>
        
        <p>By using Superagent, you represent that you are at least 18 years of age and capable of entering into a legally binding agreement.</p>
        
        <hr />
        
        <h2>3. User Responsibilities</h2>
        
        <p>You agree to:</p>
        
        <ul>
          <li>Provide accurate and complete information when registering</li>
          <li>Not use Superagent for any illegal or unauthorized purpose</li>
          <li>Be solely responsible for all activity under your account</li>
        </ul>
        
        <hr />
        
        <h2>4. Google Calendar Integration</h2>
        
        <p>To function, Superagent requires full access to your Google Calendar. You authorize us to access and interact with your calendar via Google Calendar API to perform actions on your behalf.</p>
        
        <p>Use of your Google data is governed by our <a href="/privacy">Privacy Policy</a> and Google's <a href="https://developers.google.com/terms/api-services-user-data-policy" target="_blank" rel="noopener noreferrer">User Data Policy</a>.</p>
        
        <hr />
        
        <h2>5. Data Use and Storage</h2>
        
        <p>We store limited personal data (name, email, calendar data) on secure servers to operate the service. We do not sell or share your data for advertising purposes.</p>
        
        <hr />
        
        <h2>6. Intellectual Property</h2>
        
        <p>All content, trademarks, and software on Superagent are the property of Superagent.diy or its licensors. You agree not to copy, distribute, or reverse-engineer any part of the service without our written permission.</p>
        
        <hr />
        
        <h2>7. Termination</h2>
        
        <p>We reserve the right to suspend or terminate your access to Superagent at any time, without notice or liability, if we believe you have violated these Terms or abused the service.</p>
        
        <hr />
        
        <h2>8. Disclaimers</h2>
        
        <p>Superagent is provided "as is" and "as available" without warranties of any kind, either express or implied, including but not limited to merchantability, fitness for a particular purpose, or non-infringement.</p>
        
        <p>We do not guarantee:</p>
        
        <ul>
          <li>That Superagent will always be available or error-free</li>
          <li>That calendar changes will be made correctly in all edge cases</li>
          <li>That your data will never be lost or corrupted</li>
        </ul>
        
        <p>Use at your own risk.</p>
        
        <hr />
        
        <h2>9. Limitation of Liability</h2>
        
        <p>To the maximum extent permitted by law, in no event shall Superagent.diy, its creators, or affiliates be liable for any indirect, incidental, consequential, or punitive damages, or any loss of data, business, or profits arising out of your use or inability to use the service.</p>
        
        <p>Our total liability shall not exceed the amount you paid us (if any) for using the service.</p>
        
        <hr />
        
        <h2>10. Changes to Terms</h2>
        
        <p>We may update these Terms from time to time. Continued use of the service after such updates constitutes your acceptance of the new Terms.</p>
        
        <hr />
        
        <h2>11. Governing Law</h2>
        
        <p>These Terms are governed by and construed in accordance with the laws of Bangalore, Karnataka, India, without regard to its conflict of law principles.</p>
        
        <hr />
        
        <h2>12. Contact</h2>
        
        <p>For any questions regarding these Terms, please contact:</p>
        
        <p><strong>Email:</strong> support[at]superagent.diy<br />
        <strong>Website:</strong> https://superagent.diy</p>
      </div>
    </div>
  );
};

export default Terms;
