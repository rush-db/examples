'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { DBRecordInstance } from '@rushdb/javascript-sdk'
import { useLabelColors } from '@/hooks/use-label-colors'
import { useTheme } from 'next-themes'
import { Loader, RotateCcw } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { set } from 'date-fns'
import { GraphIcon } from './ui/graph-icon'

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
      <span className="ml-2 text-muted-foreground">Loading graph...</span>
    </div>
  ),
})

interface GraphNode {
  id: string
  name: string
  label: string
  type: 'main' | 'related'
  color: string
  size: number
}

interface GraphLink {
  source: string
  target: string
  relationship: string
  color: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

interface RelationshipGraphProps {
  record: DBRecordInstance
  relations: any
  isLoading: boolean
}

export function RelationshipGraph({
  record,
  relations,
  isLoading,
}: RelationshipGraphProps) {
  const graphRef = useRef<any>()
  const containerRef = useRef<HTMLDivElement>(null)
  const { getLabelColor } = useLabelColors()
  const { theme } = useTheme()
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    links: [],
  })
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 })
  const [resetKey, setResetKey] = useState(0) // Key to force graph re-render

  // Convert label color variant to actual hex color
  const getActualColor = useCallback((colorVariant: string) => {
    const colorMap: Record<string, string> = {
      blank: '#6b7280', // gray-500
      blue: '#f59e0b', // amber-500 (replacing blue)
      green: '#22c55e', // green-500
      orange: '#f97316', // orange-500
      pink: '#ec4899', // pink-500
      red: '#ef4444', // red-500
      yellow: '#eab308', // yellow-500
    }
    return colorMap[colorVariant] || colorMap.blank
  }, [])

  // Helper function to create clean node data without fixed positions
  const createCleanNode = (
    nodeData: Omit<GraphNode, 'fx' | 'fy' | 'vx' | 'vy'>
  ): GraphNode => {
    return {
      ...nodeData,
      // Ensure no fixed position properties are set
    } as GraphNode
  }

  // Convert relations data to graph format
  useEffect(() => {
    if (!relations || isLoading) {
      setGraphData({ nodes: [], links: [] })
      return
    }

    const nodes: GraphNode[] = []
    const links: GraphLink[] = []
    const processedLabels = new Set<string>() // Track unique labels
    const processedTopologyLinks = new Set<string>() // Track unique topology links

    // Add main record as central node
    const mainRecordId = record.id()
    const mainLabel = record.label() || 'Record'
    nodes.push(
      createCleanNode({
        id: mainLabel, // Use label as ID for topology view
        name: mainLabel,
        label: mainLabel,
        type: 'main',
        color: getActualColor(getLabelColor(mainLabel)),
        size: 20,
      })
    )
    processedLabels.add(mainLabel)

    // Process relations array for topology view - group by labels and relationship types
    if (Array.isArray(relations)) {
      // First, collect all unique label combinations
      const labelRelations = new Map<
        string,
        {
          sourceLabel: string
          targetLabel: string
          type: string
          count: number
          isIncoming: boolean // Track if relationship is incoming to main record
        }
      >()

      relations.forEach((relation: any) => {
        if (
          relation &&
          relation.sourceLabel &&
          relation.targetLabel &&
          relation.sourceId && // Make sure we have sourceId
          relation.type
        ) {
          const sourceLabel = relation.sourceLabel
          const targetLabel = relation.targetLabel
          const relationType = relation.type

          const isIncoming = relation.targetId === mainRecordId

          const topologyKey = `${sourceLabel}-${targetLabel}-${relationType}-${isIncoming ? 'in' : 'out'}`

          if (labelRelations.has(topologyKey)) {
            labelRelations.get(topologyKey)!.count++
          } else {
            labelRelations.set(topologyKey, {
              sourceLabel: sourceLabel,
              targetLabel: targetLabel,
              type: relationType,
              count: 1,
              isIncoming,
            })
          }
        }
      })

      // Create nodes and links based on unique label relationships
      labelRelations.forEach(
        ({ sourceLabel, targetLabel, type, count, isIncoming }) => {
          // Add source label node if not already added
          if (!processedLabels.has(sourceLabel)) {
            nodes.push(
              createCleanNode({
                id: sourceLabel,
                name: sourceLabel,
                label: sourceLabel,
                type: sourceLabel === mainLabel ? 'main' : 'related',
                color: getActualColor(getLabelColor(sourceLabel)),
                size: sourceLabel === mainLabel ? 20 : 14,
              })
            )
            processedLabels.add(sourceLabel)
          }

          // Add target label node if not already added
          if (!processedLabels.has(targetLabel)) {
            nodes.push(
              createCleanNode({
                id: targetLabel,
                name: targetLabel,
                label: targetLabel,
                type: targetLabel === mainLabel ? 'main' : 'related',
                color: getActualColor(getLabelColor(targetLabel)),
                size: targetLabel === mainLabel ? 20 : 14,
              })
            )
            processedLabels.add(targetLabel)
          }

          // Create topology link (only one per label pair + relationship type + direction)
          const topologyLinkKey = `${sourceLabel}-${targetLabel}-${type}-${isIncoming ? 'in' : 'out'}`
          if (!processedTopologyLinks.has(topologyLinkKey)) {
            links.push({
              source: sourceLabel,
              target: targetLabel,
              relationship: count > 1 ? `${type} (${count})` : type, // Show count if multiple
              color: theme === 'dark' ? '#6b7280' : '#9ca3af',
            })
            processedTopologyLinks.add(topologyLinkKey)
          }
        }
      )
    }

    setGraphData({ nodes, links })
  }, [
    relations,
    isLoading,
    record,
    getLabelColor,
    getActualColor,
    theme,
    resetKey,
  ])

  // Handle container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current
        setDimensions({
          width: clientWidth || 972,
          height: clientHeight || 400,
        })
      }
    }

    // Initial measurement
    updateDimensions()

    // Set up resize observer
    const resizeObserver = new ResizeObserver(updateDimensions)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  const handleNodeDragEnd = (node: any) => {
    // Fix the node position when dragging ends
    node.fx = node.x
    node.fy = node.y
  }

  const handleResetPositions = () => {
    // Clear fixed positions from all nodes
    if (graphRef.current && graphRef.current.graphData) {
      const currentGraphData = graphRef.current.graphData
      currentGraphData.nodes.forEach((node: any) => {
        // Remove fixed position properties to allow D3 to recalculate positions
        delete node.fx
        delete node.fy
        delete node.vx
        delete node.vy
        // Reset any accumulated forces
        delete node.x
        delete node.y
      })
    }

    // Force a complete re-render of the graph by incrementing the reset key
    // This will recreate the graph with fresh data without fixed positions
    setResetKey((prev) => prev + 1)
  }

  if (isLoading) {
    return (
      <Card className="border-border shadow-sm h-full flex flex-col">
        <CardHeader className="pb-3 flex-shrink-0">
          <CardTitle className="text-lg flex items-center gap-2">
            <GraphIcon className="h-4 w-4" /> Relationship Graph
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 min-h-0 flex items-center justify-center">
          <div className="flex items-center">
            <Loader className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">
              Loading relationships...
            </span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (graphData.nodes.length <= 1) {
    return (
      <Card className="border-border shadow-sm h-full flex flex-col">
        <CardHeader className="pb-3 flex-shrink-0">
          <CardTitle className="text-lg flex items-center gap-2">
            <GraphIcon className="h-4 w-4" /> Relationship Graph
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 min-h-0 flex items-center justify-center text-muted-foreground">
          <div className="text-center">
            <div className="text-sm">No relationships found</div>
            <div className="text-xs mt-1">
              This record doesn't have any related records
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border shadow-sm h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <GraphIcon className="h-4 w-4" />
            Relationship Graph
            <span className="text-sm font-normal text-muted-foreground ml-2">
              ({graphData.nodes.length - 1} related records)
            </span>
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetPositions}
            className="h-8 gap-2 text-xs"
          >
            <RotateCcw className="w-3 h-3" />
            Reset Layout
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0 flex-1 min-h-0 max-h-100">
        <div
          ref={containerRef}
          className="relative w-full h-full overflow-hidden"
        >
          <ForceGraph2D
            key={resetKey} // Force re-render when resetKey changes
            ref={graphRef}
            graphData={graphData}
            width={dimensions.width}
            height={dimensions.height}
            backgroundColor={'transparent'}
            nodeColor={(node: any) => node.color}
            nodeVal={(node: any) => node.size}
            linkColor={(link: any) => link.color}
            linkWidth={2}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            enableZoomInteraction={false}
            enablePanInteraction={false}
            enableNodeDrag={true}
            nodeLabel={() => ''}
            linkLabel={() => ''}
            nodeCanvasObject={(
              node: any,
              ctx: CanvasRenderingContext2D,
              globalScale: number
            ) => {
              // Scale-independent font size
              const fontSize = 12 / globalScale
              ctx.font = `${fontSize}px Inter, sans-serif`
              const textWidth = ctx.measureText(node.name).width
              const bckgDimensions = [
                textWidth + 4 / globalScale,
                fontSize + 2 / globalScale,
              ]

              // Draw node circle
              ctx.fillStyle = node.color
              ctx.beginPath()
              ctx.arc(node.x, node.y, node.size / 2, 0, 2 * Math.PI)
              ctx.fill()

              // Draw text background
              ctx.fillStyle = 'transparent'
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y - node.size / 2 - bckgDimensions[1] - 2 / globalScale,
                bckgDimensions[0],
                bckgDimensions[1]
              )

              // Draw text
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = theme === 'dark' ? '#ffffff' : '#000000'
              ctx.font = `${fontSize}px Inter, sans-serif`
              ctx.fillText(
                node.name,
                node.x,
                node.y - node.size / 2 - fontSize / 2 - 1 / globalScale
              )
            }}
            linkCanvasObject={(
              link: any,
              ctx: CanvasRenderingContext2D,
              globalScale: number
            ) => {
              const start = link.source
              const end = link.target

              // ignore unbound links
              if (typeof start !== 'object' || typeof end !== 'object') return

              // First, draw the actual link line
              ctx.strokeStyle = link.color
              ctx.lineWidth = 1
              ctx.beginPath()
              ctx.moveTo(start.x, start.y)
              ctx.lineTo(end.x, end.y)
              ctx.stroke()

              // Draw directional arrow
              const relLink = { x: end.x - start.x, y: end.y - start.y }
              const linkLength = Math.sqrt(relLink.x ** 2 + relLink.y ** 2)
              if (linkLength > 0) {
                const arrowLength = 6
                const arrowAngle = Math.atan2(relLink.y, relLink.x)

                ctx.fillStyle = link.color
                ctx.beginPath()
                ctx.moveTo(end.x, end.y)
                ctx.lineTo(
                  end.x - arrowLength * Math.cos(arrowAngle - Math.PI / 6),
                  end.y - arrowLength * Math.sin(arrowAngle - Math.PI / 6)
                )
                ctx.lineTo(
                  end.x - arrowLength * Math.cos(arrowAngle + Math.PI / 6),
                  end.y - arrowLength * Math.sin(arrowAngle + Math.PI / 6)
                )
                ctx.closePath()
                ctx.fill()
              }

              // Then draw the label if the link is long enough
              if (linkLength < 40) return

              const LABEL_NODE_MARGIN = 8
              const MAX_FONT_SIZE = 10 / globalScale // Scale-independent
              const MIN_FONT_SIZE = 6 / globalScale

              // calculate label positioning
              const textPos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2,
              }

              const maxTextLength = linkLength - LABEL_NODE_MARGIN * 2

              let textAngle = Math.atan2(relLink.y, relLink.x)
              // maintain label vertical orientation for legibility
              if (textAngle > Math.PI / 2) textAngle = -(Math.PI - textAngle)
              if (textAngle < -Math.PI / 2) textAngle = -(-Math.PI - textAngle)

              const label = link.relationship || 'related'

              // Better font size calculation
              ctx.font = `1px Inter, sans-serif`
              const estimatedFontSize = Math.min(
                MAX_FONT_SIZE,
                maxTextLength / ctx.measureText(label).width
              )

              const fontSize = Math.max(MIN_FONT_SIZE, estimatedFontSize)
              ctx.font = `${fontSize}px Inter, sans-serif`
              const textWidth = ctx.measureText(label).width
              const bckgDimensions = [
                textWidth + fontSize * 0.4,
                fontSize + fontSize * 0.2,
              ]

              // draw text label (with background rect)
              ctx.save()
              ctx.translate(textPos.x, textPos.y)
              ctx.rotate(textAngle)

              // Simple background
              ctx.fillStyle =
                theme === 'dark'
                  ? 'rgba(0, 0, 0, 0.8)'
                  : 'rgba(255, 255, 255, 0.9)'

              ctx.fillRect(
                -bckgDimensions[0] / 2,
                -bckgDimensions[1] / 2,
                bckgDimensions[0],
                bckgDimensions[1]
              )

              // Text
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = theme === 'dark' ? '#e5e7eb' : '#374151'
              ctx.font = `${fontSize}px Inter, sans-serif`
              ctx.fillText(label, 0, 0)
              ctx.restore()
            }}
            onNodeDragEnd={handleNodeDragEnd}
            cooldownTicks={100}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
          />
        </div>
      </CardContent>
    </Card>
  )
}
