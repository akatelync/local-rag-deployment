import ChatInterface from './components/ChatInterface'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 via-blue-900 to-gray-900">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(17,24,39,0.7),rgba(17,24,39,0.9))] pointer-events-none" />
      <div className="relative">
        <ChatInterface />
      </div>
    </div>
  )
}

export default App