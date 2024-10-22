import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import logoSvg from '../assets/ava.svg';

const ChatInterface = () => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
  
    const handleSubmit = async (e) => {
      e.preventDefault();
      if (!inputValue.trim()) return;
  
      const userMessage = inputValue.trim();
      setInputValue('');
      setIsLoading(true);
  
      // Add user message to chat
      setMessages(prev => [...prev, {
        type: 'user',
        content: userMessage
      }]);
  
      try {
        const response = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ question: userMessage }),
        });
  
        const data = await response.json();
  
        setMessages(prev => [...prev, {
          type: 'bot',
          content: data.response,
          sources: data.relevant_sources
        }]);
      } catch (error) {
        console.error('Error:', error);
        setMessages(prev => [...prev, {
          type: 'error',
          content: 'Sorry, there was an error processing your request.'
        }]);
      } finally {
        setIsLoading(false);
      }
    };
  
    return (
      <main className="container mx-auto p-4 max-w-3xl flex flex-col min-h-screen">
        <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg shadow-xl flex-1">
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center gap-3">
              <img 
                src={logoSvg} 
                alt="Chat Logo" 
                className="w-8 h-8 text-blue-400"
              />
              <h1 className="text-2xl font-bold text-gray-100">AVA AI</h1>
            </div>
          </div>
  
          {/* Messages */}
          <div className="p-4 space-y-4 min-h-[500px] max-h-[500px] overflow-y-auto">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-gray-100'
                      : message.type === 'error'
                      ? 'bg-red-900 text-red-100'
                      : 'bg-gray-700 text-gray-100'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 text-sm border-t border-gray-600 pt-2">
                      <p className="font-semibold text-gray-300">Relevant Sources:</p>
                      <ul className="list-disc ml-4">
                        {message.sources.map((source, idx) => (
                          <li key={idx} className="text-gray-400">{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-700 rounded-lg p-3">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                </div>
              </div>
            )}
          </div>
  
          {/* Input */}
          <div className="p-4 border-t border-gray-700">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask AVA a question..."
                className="flex-1 bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading}
                className="bg-blue-600 text-gray-100 rounded-lg px-4 py-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 transition-colors duration-200"
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        </div>
        
        {/* Footer */}
        <footer className="text-center py-4 text-gray-400">
          <p className="text-sm font-medium hover:text-blue-400 transition-colors duration-200">
            Powered by ADI
          </p>
        </footer>
      </main>
    );
  };
  
  export default ChatInterface;