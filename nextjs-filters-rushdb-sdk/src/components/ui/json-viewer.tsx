import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { a11yDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

type JsonViewerProps = {
  data: any
}

export const JsonViewer: React.FC<JsonViewerProps> = ({ data }) => {
  return (
    <SyntaxHighlighter language="json" style={a11yDark}>
      {JSON.stringify(data, null, 2)}
    </SyntaxHighlighter>
  )
}
