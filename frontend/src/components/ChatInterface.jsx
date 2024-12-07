import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Menu, Paperclip, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import logoSvg from '../assets/ava.svg';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemType, setSystemType] = useState('general');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null);
  const [fileContent, setFileContent] = useState([]);
  const textAreaRef = useRef(null);

  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.style.height = 'auto';
      textAreaRef.current.style.height = `${textAreaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const systemNames = {
    general: 'Bill Aging Assistant',
    journal: 'Transcription Assistant'
  };

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setAttachedFile(file);
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('http://localhost:8000/api/upload-pdf', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Failed to upload PDF');
        }

        const data = await response.json();
        setFileContent(data.content);
        setMessages(prev => [...prev, {
          type: 'bot',
          content: `PDF "${file.name}" successfully processed. You can now ask questions about its content.`
        }]);
      } catch (error) {
        console.error('Error uploading PDF:', error);
        setMessages(prev => [...prev, {
          type: 'error',
          content: 'Failed to process PDF file. Please try again.'
        }]);
        setAttachedFile(null);
      }
    } else {
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Please select a valid PDF file.'
      }]);
    }
  };

  const removeAttachment = () => {
    setAttachedFile(null);
    setFileContent([]);
  };

  const handleSystemChange = (newSystem) => {
    setSystemType(newSystem);
    setIsSidebarOpen(false);
    // Clear PDF content when switching away from journal system
    if (newSystem !== 'journal') {
      setAttachedFile(null);
      setFileContent([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    setMessages((prev) => [...prev, { type: 'user', content: userMessage }]);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          history: messages.map(msg => ({
            type: msg.type === 'bot' ? 'assistant' : msg.type,
            content: msg.content
          })),
          system_type: systemType,
          pdf_content: systemType === 'journal' && fileContent.length > 0 ? fileContent : undefined
        }),
      });

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          type: 'bot',
          content: data.response,
          sources: data.relevant_sources,
        },
      ]);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          type: 'error',
          content: 'Sorry, there was an error processing your request.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      <div className={`fixed lg:static lg:translate-x-0 inset-y-0 left-0 transform ${
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      } transition-transform duration-200 ease-in-out z-30 w-64 bg-white border-r border-gray-200`}>
        <div className="p-4">
          <div className="flex items-center gap-3 mb-6">
            <img src={logoSvg} alt="Logo" className="w-8 h-8" />
            <h2 className="text-xl font-semibold text-gray-800">AVA AI</h2>
          </div>
          <div className="space-y-2">
            {Object.entries(systemNames).map(([key, name]) => (
              <button
                key={key}
                onClick={() => handleSystemChange(key)}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  systemType === key
                    ? "bg-blue-100 text-blue-700"
                    : "hover:bg-gray-100 text-gray-700"
                }`}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <main className="flex-1 flex flex-col">
        <div className="container mx-auto p-4 max-w-full flex flex-col h-full">
          <div className="flex-1 flex flex-col bg-white rounded-lg shadow-lg relative overflow-hidden border border-gray-200">
            <div className="px-8 py-6 border-b border-gray-200 backdrop-blur-sm bg-white/80">
              <div className="flex items-center gap-6">
                <button
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="lg:hidden"
                >
                  <Menu className="w-6 h-6 text-gray-600" />
                </button>
                <img src={logoSvg} alt="Chat Logo" className="w-16 h-16" />
                <div>
                  <h1 className="text-4xl font-bold text-gray-700 tracking-tight">
                    {systemNames[systemType]}
                  </h1>
                  <p className="text-sm text-gray-500 mt-1.5 tracking-wide">
                    Internal Source: GPT4
                  </p>
                </div>
              </div>
            </div>

            {systemType === 'journal' && (
              <div className="px-4 py-3 border-b border-gray-200 bg-blue-50">
                <p className="text-sm text-blue-700">
                  Upload a PDF transcript to get started with the Transcription Assistant.
                </p>
              </div>
            )}

            <div className="p-4 space-y-4 flex-1 overflow-y-auto scroll-smooth">
              {messages.map((message, index) => (
                <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg p-3 shadow-md ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white markdown-content-light'
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-700 markdown-content'
                      : 'bg-gray-100 text-gray-800 markdown-content'
                  }`}>
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
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
                  <div className="bg-gray-100 rounded-lg p-3">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  </div>
                </div>
              )}
            </div>

            <div className="px-4 py-4 border-t border-gray-200">
              {systemType === 'journal' && attachedFile && (
                <div className="mb-2 flex items-center gap-2 bg-gray-50 p-2 rounded-lg">
                  <Paperclip className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-600 flex-1 truncate">
                    {attachedFile.name}
                  </span>
                  <button
                    onClick={removeAttachment}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
              <form onSubmit={handleSubmit} className="flex gap-2 items-end">
                <div className="flex-1 flex flex-col gap-2">
                <textarea
                    ref={textAreaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(e);
                      }
                    }}
                    placeholder="Ask a question..."
                    className="flex-1 bg-gray-50 text-gray-800 border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent placeholder-gray-400 transition-all duration-200 resize-none overflow-y-hidden"
                    disabled={isLoading}
                    rows={2}
                  />
                  <div className="flex items-center gap-2">
                    {systemType === 'journal' && (
                      <label className="cursor-pointer text-gray-500 hover:text-gray-700">
                        <input
                          type="file"
                          accept=".pdf"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                        <Paperclip className="w-5 h-5" />
                      </label>
                    )}
                  </div>
                </div>
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
        </div>
      </main>
    </div>
  );
};

export default ChatInterface;