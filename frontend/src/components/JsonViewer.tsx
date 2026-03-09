import React from 'react'

interface JsonViewerProps {
  content: string | object;
  editable?: boolean;
  onChange?: (value: string) => void;
  highlightFields?: string[];
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  content,
  editable = false,
  onChange,
  highlightFields = []
}) => {
  let jsonString = ''
  
  try {
    if (typeof content === 'string') {
      JSON.parse(content)
      jsonString = JSON.stringify(JSON.parse(content), null, 2)
    } else {
      jsonString = JSON.stringify(content, null, 2)
    }
  } catch (error) {
    jsonString = typeof content === 'string' ? content : JSON.stringify(content)
  }

  if (editable) {
    return (
      <textarea
        value={jsonString}
        onChange={(e) => onChange?.(e.target.value)}
        className="w-full min-h-[200px] bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm text-blue-400 resize-none focus:outline-none focus:border-gray-700"
      />
    )
  }

  const renderJsonLine = (line: string, index: number) => {
    const trimmedLine = line.trim()
    
    // Check if this line contains a highlighted field
    const isHighlighted = highlightFields.some(field => 
      trimmedLine.includes(`"${field}"`)
    )

    // Opening brace only
    if (trimmedLine === '{') {
      return (
        <div key={index} className="text-gray-500">
          {line}
        </div>
      )
    }

    // Closing brace only
    if (trimmedLine === '}' || trimmedLine === '},') {
      return (
        <div key={index} className="text-gray-500">
          {line}
        </div>
      )
    }

    // Key-value pair with string value: "key": "value"
    const stringMatch = line.match(/^(\s*)"(\w+)":\s*"([^"]*)"(,?)$/)
    if (stringMatch) {
      const [, indent, key, value, comma] = stringMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-green-950 border-l-2 border-green-500 pl-2' : ''}`}
        >
          {indent}
          <span className="text-blue-300">&quot;{key}&quot;</span>
          <span className="text-gray-500">: </span>
          <span className="text-amber-300">&quot;{value}&quot;</span>
          <span className="text-gray-500">{comma}</span>
        </div>
      )
    }

    // Key-value pair with number value: "key": 123
    const numberMatch = line.match(/^(\s*)"(\w+)":\s*(\d+)(,?)$/)
    if (numberMatch) {
      const [, indent, key, value, comma] = numberMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-green-950 border-l-2 border-green-500 pl-2' : ''}`}
        >
          {indent}
          <span className="text-blue-300">&quot;{key}&quot;</span>
          <span className="text-gray-500">: </span>
          <span className="text-green-300">{value}</span>
          <span className="text-gray-500">{comma}</span>
        </div>
      )
    }

    // Key-value pair with boolean value: "key": true/false
    const boolMatch = line.match(/^(\s*)"(\w+)":\s*(true|false)(,?)$/)
    if (boolMatch) {
      const [, indent, key, value, comma] = boolMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-green-950 border-l-2 border-green-500 pl-2' : ''}`}
        >
          {indent}
          <span className="text-blue-300">&quot;{key}&quot;</span>
          <span className="text-gray-500">: </span>
          <span className="text-purple-300">{value}</span>
          <span className="text-gray-500">{comma}</span>
        </div>
      )
    }

    // Key-value pair with null value: "key": null
    const nullMatch = line.match(/^(\s*)"(\w+)":\s*(null)(,?)$/)
    if (nullMatch) {
      const [, indent, key, value, comma] = nullMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-green-950 border-l-2 border-green-500 pl-2' : ''}`}
        >
          {indent}
          <span className="text-blue-300">&quot;{key}&quot;</span>
          <span className="text-gray-500">: </span>
          <span className="text-gray-500">{value}</span>
          <span className="text-gray-500">{comma}</span>
        </div>
      )
    }

    // Empty line
    if (trimmedLine === '') {
      return <div key={index}>&nbsp;</div>
    }

    // Fallback: render as plain text
    return (
      <div
        key={index}
        className={`text-gray-400 ${isHighlighted ? 'bg-green-950 border-l-2 border-green-500 pl-2' : ''}`}
      >
        {line}
      </div>
    )
  }

  const lines = jsonString.split('\n')

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-auto max-h-[300px]">
      {lines.map((line, index) => renderJsonLine(line, index))}
    </div>
  )
}
