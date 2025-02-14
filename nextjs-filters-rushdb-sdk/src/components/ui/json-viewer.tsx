import React from 'react'
import JsonView from '@uiw/react-json-view'
import { nordTheme } from '@uiw/react-json-view/nord'

type JsonViewerProps = {
  data: any
}

export const JsonViewer: React.FC<JsonViewerProps> = ({ data }) => {
  return (
    <JsonView
      value={data}
      style={nordTheme}
      collapsed={1}
      displayObjectSize={false}
      displayDataTypes={false}
      enableClipboard={false}
    >
      <JsonView.Colon
        render={(props, { parentValue, value, keyName }) => {
          if (Array.isArray(parentValue) && props.children == ':') {
            return <span />
          }
          return <span {...props} />
        }}
      />
      <JsonView.KeyName
        render={({ ...props }, { parentValue, value, keyName }) => {
          if (Array.isArray(parentValue) && Number.isFinite(props.children)) {
            return <span />
          }
          // @ts-ignore
          return <span {...props} />
        }}
      />
    </JsonView>
  )
}
