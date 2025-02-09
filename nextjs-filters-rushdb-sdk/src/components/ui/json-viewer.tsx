import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { a11yDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

type JsonViewerProps = {
  data: any
}

export const JsonViewer: React.FC<JsonViewerProps> = ({ data }) => {
  console.log(data)

  return (
    <SyntaxHighlighter language="json" style={a11yDark}>
      {'responseData' in data
        ? JSON.stringify({ ...data.responseData }, null, 2)
        : JSON.stringify(
            { method: data.method, path: data.path, headers: data.headers },
            null,
            2
          )}
    </SyntaxHighlighter>
  )
}
