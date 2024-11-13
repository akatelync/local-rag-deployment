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
          <div className="bg-white/90 backdrop-blur rounded-lg shadow-lg flex-1 relative overflow-hidden transition-all duration-300 ease-in-out border border-gray-200">
            {/* Header */}
            <div className="px-8 py-6 border-b border-gray-200 backdrop-blur-sm bg-white/80">
              <div className="flex items-center gap-6">
                <img 
                  src={logoSvg} 
                  alt="Chat Logo" 
                  className="w-16 h-16 text-blue-600"
                />
                <div>
                  <h1 className="text-4xl font-bold text-gray-700 tracking-tight">AVA AI</h1>
                  <p className="text-sm text-gray-500 mt-1.5 tracking-wide">Internal Source: GPT4</p>
                </div>
              </div>
            </div>
    
            {/* Messages */}
            <div className="p-4 space-y-4 min-h-[500px] max-h-[500px] overflow-y-auto scroll-smooth">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 shadow-md transition-all duration-200 ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 text-sm border-t border-gray-200 pt-2">
                        <p className="font-semibold text-gray-700">Relevant Sources:</p>
                        <ul className="list-disc ml-4">
                          {message.sources.map((source, idx) => (
                            <li key={idx} className="text-gray-600">{source}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-3 shadow-md">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  </div>
                </div>
              )}
            </div>
    
            {/* Input */}
            <div className="p-4 border-t border-gray-200 backdrop-blur-sm bg-white/80">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Ask AVA a question..."
                  className="flex-1 bg-gray-50 text-gray-800 border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent placeholder-gray-400 transition-all duration-200"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading}
                  className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2 focus:ring-offset-white disabled:opacity-50 transition-all duration-200 shadow-md"
                >
                  <Send className="w-5 h-5" />
                </button>
              </form>
            </div>
          </div>
          
          {/* Footer */}
          <footer className="text-center py-4 text-gray-600">
            <p className="text-sm font-medium hover:text-blue-600 transition-colors duration-200">
              Powered by ADI
            </p>
          </footer>
        </main>
      );
    };
    
    export default ChatInterface;