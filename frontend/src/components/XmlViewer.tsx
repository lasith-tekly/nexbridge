import React from 'react'

interface XmlViewerProps {
  content: string;
  editable?: boolean;
  onChange?: (value: string) => void;
  highlightFields?: string[];
}

export const XmlViewer: React.FC<XmlViewerProps> = ({
  content,
  editable = false,
  onChange,
  highlightFields = []
}) => {
  if (editable) {
    return (
      <textarea
        value={content}
        onChange={(e) => onChange?.(e.target.value)}
        className="w-full min-h-[200px] bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm text-green-400 resize-none focus:outline-none focus:border-gray-700"
      />
    )
  }

  const renderXmlLine = (line: string, index: number) => {
    const trimmedLine = line.trim()
    
    // Check if this line contains a highlighted field
    const isHighlighted = highlightFields.some(field => 
      trimmedLine.includes(`<${field}>`) || trimmedLine.includes(`</${field}>`)
    )

    // Opening tag with content: <tag>content</tag>
    const openCloseMatch = trimmedLine.match(/^<(\w+)>(.+)<\/(\w+)>$/)
    if (openCloseMatch) {
      const [, openTag, content, closeTag] = openCloseMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-red-950 border-l-2 border-red-500 pl-2' : ''}`}
        >
          <span className="text-gray-500">&lt;</span>
          <span className="text-blue-300">{openTag}</span>
          <span className="text-gray-500">&gt;</span>
          <span className="text-green-300">{content}</span>
          <span className="text-gray-500">&lt;/</span>
          <span className="text-blue-300">{closeTag}</span>
          <span className="text-gray-500">&gt;</span>
        </div>
      )
    }

    // Opening tag only: <tag>
    const openMatch = trimmedLine.match(/^<(\w+)>$/)
    if (openMatch) {
      const [, tag] = openMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-red-950 border-l-2 border-red-500 pl-2' : ''}`}
        >
          <span className="text-gray-500">&lt;</span>
          <span className="text-blue-300">{tag}</span>
          <span className="text-gray-500">&gt;</span>
        </div>
      )
    }

    // Closing tag only: </tag>
    const closeMatch = trimmedLine.match(/^<\/(\w+)>$/)
    if (closeMatch) {
      const [, tag] = closeMatch
      return (
        <div
          key={index}
          className={`${isHighlighted ? 'bg-red-950 border-l-2 border-red-500 pl-2' : ''}`}
        >
          <span className="text-gray-500">&lt;/</span>
          <span className="text-blue-300">{tag}</span>
          <span className="text-gray-500">&gt;</span>
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
        className={`text-gray-400 ${isHighlighted ? 'bg-red-950 border-l-2 border-red-500 pl-2' : ''}`}
      >
        {line}
      </div>
    )
  }

  const lines = content.split('\n')

  return (
    <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-auto max-h-[300px]">
      {lines.map((line, index) => renderXmlLine(line, index))}
    </div>
  )
}
