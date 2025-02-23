import React, { useState, useRef, useEffect } from 'react';

const CliChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [cliOutput, setCliOutput] = useState('');
  const messagesEndRef = useRef(null);
  const cliRef = useRef(null);

  // Auto-scroll messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Process commands and natural language input
  const processInput = async (text) => {
    // Add user message
    setMessages(prev => [...prev, { type: 'user', text }]);

    // Process command or query
    let response;
    if (text.startsWith('/')) {
      // Handle CLI commands
      const command = text.slice(1);
      response = await executeCliCommand(command);
      setCliOutput(prev => prev + '\n' + response);
    } else {
      // Handle natural language queries
      response = await processNaturalLanguage(text);
    }

    // Add assistant response
    setMessages(prev => [...prev, { type: 'assistant', text: response }]);
  };

  // Execute RABCDAsm CLI commands
  const executeCliCommand = async (command) => {
    const commands = {
      'extract': 'abcexport',
      'disassemble': 'rabcdasm',
      'assemble': 'rabcasm',
      'replace': 'abcreplace',
      'decompress': 'swfdecompress'
    };

    const baseCmd = command.split(' ')[0];
    if (commands[baseCmd]) {
      return `Executing ${commands[baseCmd]} ${command.slice(baseCmd.length)}...`;
    }
    return 'Unknown command';
  };

  // Process natural language input
  const processNaturalLanguage = async (text) => {
    // Common RABCDAsm operations in natural language
    const patterns = {
      'extract': /extract|export|pull out/i,
      'disassemble': /disassemble|decompile|break down/i,
      'assemble': /assemble|compile|build/i,
      'analyze': /analyze|examine|look at/i
    };

    for (const [action, pattern] of Object.entries(patterns)) {
      if (pattern.test(text)) {
        return `I'll help you ${action} the SWF file. Here's the command:\n/${action} file.swf`;
      }
    }

    return "I'm not sure what you want to do. Try using specific terms like 'extract', 'disassemble', or 'analyze'.";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    processInput(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-96">
      {/* Chat and CLI split view */}
      <div className="flex flex-1 gap-4 mb-4">
        {/* Chat messages */}
        <div className="flex-1 bg-gray-100 rounded-lg p-4 overflow-y-auto">
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`mb-2 p-2 rounded ${
                msg.type === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-200 mr-8'
              }`}
            >
              {msg.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* CLI output */}
        <div 
          ref={cliRef}
          className="flex-1 bg-black text-green-400 font-mono p-4 rounded-lg overflow-y-auto whitespace-pre"
        >
          {cliOutput || 'RABCDAsm CLI ready...'}
        </div>
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter a command (/extract, /disassemble) or ask a question..."
          className="flex-1 p-2 border rounded"
        />
        <button 
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default CliChatInterface;
