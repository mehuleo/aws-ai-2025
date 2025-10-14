import React, { useState, useEffect } from 'react';

interface AgentData {
  agent_email: string;
  user_email: string;
  created_at: string;
}

const CreateExecutiveAssistant: React.FC = () => {
  const [inviteCode, setInviteCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isCheckingAgent, setIsCheckingAgent] = useState(true);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error' | ''>('');
  const [agentData, setAgentData] = useState<AgentData | null>(null);
  const [hasAgent, setHasAgent] = useState(false);

  // Check if user already has an agent on component mount
  useEffect(() => {
    checkExistingAgent();
  }, []);

  const checkExistingAgent = async () => {
    try {
      setIsCheckingAgent(true);
      
      const userEmail = localStorage.getItem('email');
      const userSid = localStorage.getItem('sid');
      
      if (!userEmail || !userSid) {
        setMessage('Authentication required. Please log in again.');
        setMessageType('error');
        setIsCheckingAgent(false);
        return;
      }

      const response = await fetch('https://api.superagent.diy/v1/getAgentEmail', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          sid: userSid
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.agent_email) {
          setAgentData({
            agent_email: data.agent_email,
            user_email: data.user_email,
            created_at: data.created_at
          });
          setHasAgent(true);
        } else {
          setHasAgent(false);
        }
      } else {
        // If 404, user doesn't have an agent yet
        if (response.status === 404) {
          setHasAgent(false);
        } else {
          const errorData = await response.json();
          setMessage(`Error checking agent status: ${errorData.error || 'Unknown error'}`);
          setMessageType('error');
        }
      }
    } catch (error) {
      console.error('Error checking existing agent:', error);
      setMessage('Failed to check agent status. Please try again.');
      setMessageType('error');
    } finally {
      setIsCheckingAgent(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inviteCode.trim()) {
      setMessage('Please enter an invite code');
      setMessageType('error');
      return;
    }

    setIsLoading(true);
    setMessage('');
    setMessageType('');

    try {
      const userEmail = localStorage.getItem('email');
      const userSid = localStorage.getItem('sid');
      
      if (!userEmail || !userSid) {
        setMessage('Authentication required. Please log in again.');
        setMessageType('error');
        setIsLoading(false);
        return;
      }

      const response = await fetch('https://api.superagent.diy/v1/validateInvite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          sid: userSid,
          invite_code: inviteCode
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.user && data.user.agent_email) {
          setMessage('Invite code validated successfully! Your executive assistant has been created.');
          setMessageType('success');
          setInviteCode('');
          
          // Update agent data and show agent exists state
          setAgentData({
            agent_email: data.user.agent_email,
            user_email: data.user.email,
            created_at: new Date().toISOString()
          });
          setHasAgent(true);
        } else {
          setMessage('Failed to create agent. Please try again.');
          setMessageType('error');
        }
      } else {
        const errorData = await response.json();
        setMessage(errorData.error || 'Failed to validate invite code. Please try again.');
        setMessageType('error');
      }
      
    } catch (error) {
      console.error('Error validating invite code:', error);
      setMessage('Failed to validate invite code. Please try again.');
      setMessageType('error');
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state while checking for existing agent
  if (isCheckingAgent) {
    return (
      <div className="dashboard-section">
        <h1 className="section-title">Create Executive Assistant</h1>
        <div className="section-content">
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Checking your agent status...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show agent exists UI
  if (hasAgent && agentData) {
    return (
      <div className="dashboard-section">
        <h1 className="section-title">Your Executive Assistant</h1>
        <div className="section-content">
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Your Executive Assistant is Ready!
                </h2>
                <p className="text-gray-600 text-sm">
                  You already have an AI executive assistant set up and ready to help you.
                </p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Your Agent Email:</p>
                  <div className="bg-white border border-gray-200 rounded-md p-3 mb-3">
                    <code className="text-purple-600 font-mono text-sm break-all">
                      {agentData.agent_email}
                    </code>
                  </div>
                  <button
                    onClick={() => navigator.clipboard.writeText(agentData.agent_email)}
                    className="text-purple-600 hover:text-purple-700 text-sm font-medium"
                  >
                    Copy Email Address
                  </button>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">How to Use Your Assistant</h3>
                <p className="text-blue-800 text-sm mb-3">
                  Simply send an email to your agent email address with any task or question, and your AI assistant will help you get things done!
                </p>
                <div className="text-sm text-blue-700">
                  <p className="mb-1">• Schedule meetings and manage your calendar</p>
                  <p className="mb-1">• Get help with research and analysis</p>
                  <p className="mb-1">• Draft emails and documents</p>
                  <p>• And much more!</p>
                </div>
              </div>

              {message && (
                <div className={`mt-4 p-3 rounded-md text-sm ${
                  messageType === 'success' 
                    ? 'bg-green-50 text-green-800 border border-green-200' 
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  {message}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show invite code form for users without an agent
  return (
    <div className="dashboard-section">
      <h1 className="section-title">Create Executive Assistant</h1>
      <div className="section-content">
        <div className="max-w-md mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Create Your Executive Assistant
              </h2>
              <p className="text-gray-600 text-sm">
                Enter your invite code to create a personalized AI executive assistant
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="invite-code" className="block text-sm font-medium text-gray-700 mb-2">
                  Invite Code
                </label>
                <input
                  type="text"
                  id="invite-code"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  placeholder="Enter your invite code"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  disabled={isLoading}
                />
              </div>

              {message && (
                <div className={`p-3 rounded-md text-sm ${
                  messageType === 'success' 
                    ? 'bg-green-50 text-green-800 border border-green-200' 
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  {message}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || !inviteCode.trim()}
                className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Validating...
                  </div>
                ) : (
                  'Create Assistant'
                )}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-2">Don't have an invite code?</p>
                <button className="text-purple-600 hover:text-purple-700 text-sm font-medium">
                  Request Access
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateExecutiveAssistant;
