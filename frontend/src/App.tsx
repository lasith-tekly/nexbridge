import React from 'react'

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="bg-gray-900 border-b border-gray-800 px-8 py-6">
        <h1 className="text-3xl font-bold text-white">NexBridge</h1>
        <p className="text-gray-400 mt-2">Governed AI Transformation for Any Protocol</p>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-3 gap-6 h-[calc(100vh-200px)]">
          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-200">Input Panel</h2>
            <div className="text-gray-500 text-center mt-20">
              XML Input Placeholder
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-200">Pipeline Panel</h2>
            <div className="text-gray-500 text-center mt-20">
              Agent Pipeline Placeholder
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-200">Output Panel</h2>
            <div className="text-gray-500 text-center mt-20">
              JSON Output Placeholder
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
